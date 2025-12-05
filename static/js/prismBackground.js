// static/js/prismBackground.js
// Fondo tipo "Prism" usando Three.js + el fragment shader original

(function () {
  function initPrism() {
    const container = document.getElementById("prism-bg");
    if (!container) return;
    if (typeof THREE === "undefined") {
      console.warn("THREE no está cargado; no se puede inicializar Prism.");
      return;
    }

    // Parámetros base del efecto (puedes ajustarlos)
    const params = {
      height: 3.5,
      baseWidth: 5.5,
      glow: 1.0,
      noise: 0.5,
      scale: 3.6,
      hueShift: 0.0,
      colorFrequency: 1.0,
      bloom: 1.0,
      timeScale: 0.5,
      offsetX: 0,
      offsetY: 0,
      useBaseWobble: 1 // 1 = animación activada
    };

    const H = Math.max(0.001, params.height);
    const BW = Math.max(0.001, params.baseWidth);
    const BASE_HALF = BW * 0.5;
    const GLOW = Math.max(0.0, params.glow);
    const NOISE = Math.max(0.0, params.noise);
    const SAT = 1.5;
    const SCALE = Math.max(0.001, params.scale);
    const HUE = params.hueShift || 0.0;
    const CFREQ = Math.max(0.0, params.colorFrequency || 1.0);
    const BLOOM = Math.max(0.0, params.bloom || 1.0);
    const TS = Math.max(0.0, params.timeScale || 1.0);

    // Renderer
    const renderer = new THREE.WebGLRenderer({
      antialias: false,
      alpha: true
    });
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    renderer.setPixelRatio(dpr);
    renderer.setClearColor(0x000000, 0); // totalmente transparente
    container.appendChild(renderer.domElement);

    // Escena y cámara ortográfica para quad fullscreen
    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

    const geometry = new THREE.PlaneGeometry(2, 2);

    // Uniforms
    const iResolution = new THREE.Vector2(1, 1);
    const offsetPx = new THREE.Vector2(params.offsetX * dpr, params.offsetY * dpr);

    const uniforms = {
      iResolution: { value: iResolution },
      iTime: { value: 0.0 },

      uHeight: { value: H },
      uBaseHalf: { value: BASE_HALF },
      uUseBaseWobble: { value: params.useBaseWobble ? 1 : 0 },
      uRot: { value: new THREE.Matrix3().identity() },
      uGlow: { value: GLOW },
      uOffsetPx: { value: offsetPx },
      uNoise: { value: NOISE },
      uSaturation: { value: SAT },
      uScale: { value: SCALE },
      uHueShift: { value: HUE },
      uColorFreq: { value: CFREQ },
      uBloom: { value: BLOOM },
      uCenterShift: { value: H * 0.25 },
      uInvBaseHalf: { value: 1.0 / BASE_HALF },
      uInvHeight: { value: 1.0 / H },
      uMinAxis: { value: Math.min(BASE_HALF, H) },
      uPxScale: { value: 1.0 }, // se recalcula en resize
      uTimeScale: { value: TS }
    };

    // Vertex shader simple para fullscreen quad
    const vertexShader = `
      varying vec2 vUv;
      void main() {
        vUv = uv;
        gl_Position = vec4(position, 1.0);
      }
    `;

    // Fragment shader de Prism (ligeramente adaptado, pero igual visualmente)
    const fragmentShader = `
      precision highp float;

      uniform vec2  iResolution;
      uniform float iTime;

      uniform float uHeight;
      uniform float uBaseHalf;
      uniform mat3  uRot;
      uniform int   uUseBaseWobble;
      uniform float uGlow;
      uniform vec2  uOffsetPx;
      uniform float uNoise;
      uniform float uSaturation;
      uniform float uScale;
      uniform float uHueShift;
      uniform float uColorFreq;
      uniform float uBloom;
      uniform float uCenterShift;
      uniform float uInvBaseHalf;
      uniform float uInvHeight;
      uniform float uMinAxis;
      uniform float uPxScale;
      uniform float uTimeScale;

      vec4 tanh4(vec4 x){
        vec4 e2x = exp(2.0*x);
        return (e2x - 1.0) / (e2x + 1.0);
      }

      float rand(vec2 co){
        return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453123);
      }

      float sdOctaAnisoInv(vec3 p){
        vec3 q = vec3(abs(p.x) * uInvBaseHalf, abs(p.y) * uInvHeight, abs(p.z) * uInvBaseHalf);
        float m = q.x + q.y + q.z - 1.0;
        return m * uMinAxis * 0.5773502691896258;
      }

      float sdPyramidUpInv(vec3 p){
        float oct = sdOctaAnisoInv(p);
        float halfSpace = -p.y;
        return max(oct, halfSpace);
      }

      mat3 hueRotation(float a){
        float c = cos(a), s = sin(a);
        mat3 W = mat3(
          0.299, 0.587, 0.114,
          0.299, 0.587, 0.114,
          0.299, 0.587, 0.114
        );
        mat3 U = mat3(
           0.701, -0.587, -0.114,
          -0.299,  0.413, -0.114,
          -0.300, -0.588,  0.886
        );
        mat3 V = mat3(
           0.168, -0.331,  0.500,
           0.328,  0.035, -0.500,
          -0.497,  0.296,  0.201
        );
        return W + U * c + V * s;
      }

      void main(){
        // Coordenadas en espacio pantalla, con offset y escala
        vec2 f = (gl_FragCoord.xy - 0.5 * iResolution.xy - uOffsetPx) * uPxScale;

        float z = 5.0;
        float d = 0.0;

        vec3 p;
        vec4 o = vec4(0.0);

        float centerShift = uCenterShift;
        float cf = uColorFreq;

        mat2 wob = mat2(1.0);
        if (uUseBaseWobble == 1) {
          float t = iTime * uTimeScale;
          float c0 = cos(t + 0.0);
          float c1 = cos(t + 33.0);
          float c2 = cos(t + 11.0);
          wob = mat2(c0, c1, c2, c0);
        }

        const int STEPS = 100;
        for (int i = 0; i < STEPS; i++) {
          p = vec3(f, z);
          p.xz = p.xz * wob;
          p = uRot * p;
          vec3 q = p;
          q.y += centerShift;
          d = 0.1 + 0.2 * abs(sdPyramidUpInv(q));
          z -= d;
          o += (sin((p.y + z) * cf + vec4(0.0, 1.0, 2.0, 3.0)) + 1.0) / d;
        }

        o = tanh4(o * o * (uGlow * uBloom) / 1e5);

        vec3 col = o.rgb;
        float n = rand(gl_FragCoord.xy + vec2(iTime));
        col += (n - 0.5) * uNoise;
        col = clamp(col, 0.0, 1.0);

        float L = dot(col, vec3(0.2126, 0.7152, 0.0722));
        col = clamp(mix(vec3(L), col, uSaturation), 0.0, 1.0);

        if(abs(uHueShift) > 0.0001){
          col = clamp(hueRotation(uHueShift) * col, 0.0, 1.0);
        }

        gl_FragColor = vec4(col, o.a);
      }
    `;

    const material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms,
      transparent: true
    });

    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);

    function handleResize() {
      const w = container.clientWidth || window.innerWidth || 1;
      const h = container.clientHeight || window.innerHeight || 1;
      renderer.setSize(w, h, false);

      iResolution.set(w * dpr, h * dpr);
      uniforms.uPxScale.value = 1.0 / ((iResolution.y || 1.0) * 0.1 * SCALE);
    }

    handleResize();
    window.addEventListener("resize", handleResize);

    const clock = new THREE.Clock();

    function animate() {
      const t = clock.getElapsedTime();
      uniforms.iTime.value = t;
      renderer.render(scene, camera);
      requestAnimationFrame(animate);
    }

    animate();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPrism);
  } else {
    initPrism();
  }
})();
