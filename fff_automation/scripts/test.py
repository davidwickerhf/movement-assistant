from fff_automation.modules import encryption

value = 1234
value_b = 'AbC2'

print(value)
encrypted = encryption.encrypt(value)
print('Encrypted: ', encrypted)

decrypted = encryption.decrypt(encrypted)
print('Decrypted: ', decrypted)

encrypted = encryption.encrypt(value)
print('Encrypt Twice: ', encrypted)