from abc import ABC, abstractmethod


class OutputInterface(ABC):
    @abstractmethod
    def on_new_song(self, name, artist):
        pass

    @abstractmethod
    def on_lyric(self, lyric):
        pass

    @abstractmethod
    def on_no_lyrics_found(self):
        pass

    @abstractmethod
    def on_end_of_song(self):
        pass


class TerminalOutput(OutputInterface):
    def on_lyric(self, lyric):
        print(lyric)

    def on_end_of_song(self):
        print("END OF SONG")

    def on_new_song(self, name, artist):
        print("NEW SONG: ")
        print(name)
        print(artist)

    def on_no_lyrics_found(self):
        print("COULD NOT FIND LYRICS. NO DISPLAY.")