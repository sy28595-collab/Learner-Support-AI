from src.preprocessor import clean_text, preprocess_text

text = "I cannot access my Python course! Please help."

print("ORIGINAL TEXT:")
print(text)

print("\nCLEANED TEXT:")
print(clean_text(text))

print("\nPROCESSED TOKENS:")
print(preprocess_text(text))
