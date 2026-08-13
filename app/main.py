from app.config import HF_TOKEN


def main():
    print("Document Intelligence Agent")
    
    if HF_TOKEN:
        print("HF token loaded successfully.")
    else:
        print("HF token is missing.")


if __name__ == "__main__":
    main()