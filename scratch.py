import gdown

url = "https://drive.google.com/file/d/1v58P8d85W3H0tY5vO6uD7H660q6Vq7E-/view?usp=sharing"
output = "test.pdf"

print("Trying gdown...")
res = gdown.download(url, output, quiet=False, fuzzy=True)
print("Result:", res)
import os
if os.path.exists(output):
    print("Size:", os.path.getsize(output))
else:
    print("File not found")
