import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QDialog, QVBoxLayout
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl

class VideoPlayerWindow(QDialog):
    def __init__(self):
        super().__init__()

        # Membuat QMediaPlayer dan QMediaContent
        self.player = QMediaPlayer()
        self.media_content = QMediaContent(QUrl.fromLocalFile("video.mp4"))

        # Mengatur media content pada player
        self.player.setMedia(self.media_content)

        # Membuat tombol play/pause
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_playback)

        # Membuat layout
        layout = QVBoxLayout()
        layout.addWidget(self.play_button)
        self.setLayout(layout)

    def toggle_playback(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_button.setText("Play")
        else:
            self.player.play()
            self.play_button.setText("Pause")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Membuat tombol "Play"
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.open_video_player)

        # Mengatur tombol "Play" sebagai konten utama jendela
        self.setCentralWidget(self.play_button)

    def open_video_player(self):
        # Membuat subwindow VideoPlayerWindow
        video_player_window = VideoPlayerWindow()
        video_player_window.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
