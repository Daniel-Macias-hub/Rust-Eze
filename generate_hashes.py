# generate_hashes.py
from werkzeug.security import generate_password_hash

admin_password = "Admin123!"
seller_password = "Vendedor123!"
client_password = "Cliente123!"

print("Admin hash:")
print(generate_password_hash(admin_password))
print("\nVendedor hash:")
print(generate_password_hash(seller_password))
print("\nCliente hash:")
print(generate_password_hash(client_password))
