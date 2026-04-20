import requests

url = "https://blockstream.info/api/blocks/tip/hash"
tip = requests.get(url).text.strip()
block = requests.get(f"https://blockstream.info/api/block/{tip}").json()

print(f"Height: {block['height']}")
print(f"Hash: {block['id']}")
print(f"Bits (target): {block['bits']}")
print(f"Nonce: {block['nonce']}")
print(f"Tx count: {block['tx_count']}")
