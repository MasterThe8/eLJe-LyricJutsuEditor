from PyQt5.QtWidgets import QApplication, QColorDialog

app = QApplication([])

# Tampilkan dialog Color Picker
color = QColorDialog.getColor()

# Cek apakah pengguna telah memilih warna
if color.isValid():
    # Ambil nilai RGB dari warna yang dipilih
    red = color.red()
    green = color.green()
    blue = color.blue()
    alpha = color.alpha()

    # Tampilkan nilai RGB dan alpha pada konsol
    print(f"Red: {red}")
    print(f"Green: {green}")
    print(f"Blue: {blue}")
    print(f"Alpha: {alpha}")

app.exec_()
