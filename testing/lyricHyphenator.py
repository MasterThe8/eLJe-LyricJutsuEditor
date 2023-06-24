def lyric_hyphenator(word):
    vowels = "aiueoAIUEO"  # Daftar huruf vokal
    hyphen = "-"  # Tanda pemenggalan kata

    # Menyimpan hasil pemenggalan kata
    hyphenated_word = ""

    # Melakukan iterasi untuk setiap karakter dalam kata
    for i in range(len(word)):
        current_char = word[i]
        next_char = "" if i == len(word) - 1 else word[i + 1]

        # Menambahkan karakter saat ini ke hasil pemenggalan kata
        hyphenated_word += current_char

        # Memeriksa apakah karakter saat ini adalah vokal dan karakter selanjutnya adalah konsonan
        if current_char in vowels and next_char not in vowels:
            # Menambahkan tanda pemenggalan kata setelah karakter saat ini
            hyphenated_word += hyphen

    return hyphenated_word


# Contoh penggunaan
kata = "Ki ni natte shimau no wa naze"
hasil = lyric_hyphenator(kata)
print(hasil)
