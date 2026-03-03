import wfdb
import os

# create datasets folder if not exists
os.makedirs("../datasets/mitbih", exist_ok=True)

print("Downloading MIT-BIH dataset...")

wfdb.dl_database(
    "mitdb",
    dl_dir="../datasets/mitbih"
)

print("Download complete!")
