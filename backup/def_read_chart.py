def read_chart(self, file_chart):
    with open(file_chart, 'rb') as f:
        file_contents = f.read()
        encoding = chardet.detect(file_contents)['encoding']
        
        sync_track_text = file_contents.decode()[file_contents.decode().find('[SyncTrack]'):file_contents.decode().find('}', file_contents.decode().find('[SyncTrack]'))+1]
        song_text = file_contents.decode()[file_contents.decode().find('[Song]'):file_contents.decode().find('}', file_contents.decode().find('[Song]'))+1]
        
        events_text = file_contents.decode()[file_contents.decode().find('[Events]'):file_contents.decode().find('}', file_contents.decode().find('[Events]'))+1]
        events_split = events_text.split('{')
        songrex = 'songrex'
        events_display = events_split[1].replace('}','')
        events_temp = events_split[0] + '{\n' + songrex +'\n}\n'
        
        GlobalText.song = song_text + '\n'
        GlobalText.sync_track = sync_track_text + '\n'
        GlobalText.events = events_temp + '\n'
        
        # Single (Lead Guitar)
        expert_single = file_contents.decode()[file_contents.decode().find('[ExpertSingle]'):file_contents.decode().find('}', file_contents.decode().find('[ExpertSingle]'))+1]
        hard_single = file_contents.decode()[file_contents.decode().find('[HardSingle]'):file_contents.decode().find('}', file_contents.decode().find('[HardSingle]'))+1]
        medium_single = file_contents.decode()[file_contents.decode().find('[MediumSingle]'):file_contents.decode().find('}', file_contents.decode().find('[MediumSingle]'))+1]
        easy_single = file_contents.decode()[file_contents.decode().find('[EasySingle]'):file_contents.decode().find('}', file_contents.decode().find('[EasySingle]'))+1]
        
        # DoubleGuitar
        expert_double_guitar = file_contents.decode()[file_contents.decode().find('[ExpertDoubleGuitar]'):file_contents.decode().find('}', file_contents.decode().find('[ExpertDoubleGuitar]'))+1]
        hard_double_guitar = file_contents.decode()[file_contents.decode().find('[HardDoubleGuitar]'):file_contents.decode().find('}', file_contents.decode().find('[HardDoubleGuitar]'))+1]
        medium_double_guitar = file_contents.decode()[file_contents.decode().find('[MediumDoubleGuitar]'):file_contents.decode().find('}', file_contents.decode().find('[MediumDoubleGuitar]'))+1]
        easy_double_guitar = file_contents.decode()[file_contents.decode().find('[EasyDoubleGuitar]'):file_contents.decode().find('}', file_contents.decode().find('[EasyDoubleGuitar]'))+1]
        
        # DoubleBass
        expert_double_bass = file_contents.decode()[file_contents.decode().find('[ExpertDoubleBass]'):file_contents.decode().find('}', file_contents.decode().find('[ExpertDoubleBass]'))+1]
        hard_double_bass = file_contents.decode()[file_contents.decode().find('[HardDoubleBass]'):file_contents.decode().find('}', file_contents.decode().find('[HardDoubleBass]'))+1]
        medium_double_bass = file_contents.decode()[file_contents.decode().find('[MediumDoubleBass]'):file_contents.decode().find('}', file_contents.decode().find('[MediumDoubleBass]'))+1]
        easy_double_bass = file_contents.decode()[file_contents.decode().find('[EasyDoubleBass]'):file_contents.decode().find('}', file_contents.decode().find('[EasyDoubleBass]'))+1]
        
        # DoubleRhythm
        expert_double_rhythm = file_contents.decode()[file_contents.decode().find('[ExpertDoubleRhythm]'):file_contents.decode().find('}', file_contents.decode().find('[ExpertDoubleRhythm]'))+1]
        hard_double_rhythm = file_contents.decode()[file_contents.decode().find('[HardDoubleRhythm]'):file_contents.decode().find('}', file_contents.decode().find('[HardDoubleRhythm]'))+1]
        medium_double_rhythm = file_contents.decode()[file_contents.decode().find('[MediumDoubleRhythm]'):file_contents.decode().find('}', file_contents.decode().find('[MediumDoubleRhythm]'))+1]
        easy_double_rhythm = file_contents.decode()[file_contents.decode().find('[EasyDoubleRhythm]'):file_contents.decode().find('}', file_contents.decode().find('[EasyDoubleRhythm]'))+1]
        
        # Keyboard
        expert_keyboard = file_contents.decode()[file_contents.decode().find('[ExpertKeyboard]'):file_contents.decode().find('}', file_contents.decode().find('[ExpertKeyboard]'))+1]
        hard_keyboard = file_contents.decode()[file_contents.decode().find('[HardKeyboard]'):file_contents.decode().find('}', file_contents.decode().find('[HardKeyboard]'))+1]
        medium_keyboard = file_contents.decode()[file_contents.decode().find('[MediumKeyboard]'):file_contents.decode().find('}', file_contents.decode().find('[MediumKeyboard]'))+1]
        easy_keyboard = file_contents.decode()[file_contents.decode().find('[EasyKeyboard]'):file_contents.decode().find('}', file_contents.decode().find('[EasyKeyboard]'))+1]
        
        # Drums
        expert_drums = file_contents.decode()[file_contents.decode().find('[ExpertDrums]'):file_contents.decode().find('}', file_contents.decode().find('[ExpertDrums]'))+1]
        hard_drums = file_contents.decode()[file_contents.decode().find('[HardDrums]'):file_contents.decode().find('}', file_contents.decode().find('[HardDrums]'))+1]
        medium_drums = file_contents.decode()[file_contents.decode().find('[MediumDrums]'):file_contents.decode().find('}', file_contents.decode().find('[MediumDrums]'))+1]
        easy_drums = file_contents.decode()[file_contents.decode().find('[EasyDrums]'):file_contents.decode().find('}', file_contents.decode().find('[EasyDrums]'))+1]
        
        # GHLGuitar
        expert_ghl_guitar = file_contents.decode()[file_contents.decode().find('[ExpertGHLGuitar]'):file_contents.decode().find('}', file_contents.decode().find('[ExpertGHLGuitar]'))+1]
        hard_ghl_guitar = file_contents.decode()[file_contents.decode().find('[HardGHLGuitar]'):file_contents.decode().find('}', file_contents.decode().find('[HardGHLGuitar]'))+1]
        medium_ghl_guitar = file_contents.decode()[file_contents.decode().find('[MediumGHLGuitar]'):file_contents.decode().find('}', file_contents.decode().find('[MediumGHLGuitar]'))+1]
        easy_ghl_guitar = file_contents.decode()[file_contents.decode().find('[EasyGHLGuitar]'):file_contents.decode().find('}', file_contents.decode().find('[EasyGHLGuitar]'))+1]
        
        # GHLBass
        expert_ghl_bass = file_contents.decode()[file_contents.decode().find('[ExpertGHLBass]'):file_contents.decode().find('}', file_contents.decode().find('[ExpertGHLBass]'))+1]
        hard_ghl_bass = file_contents.decode()[file_contents.decode().find('[HardGHLBass]'):file_contents.decode().find('}', file_contents.decode().find('[HardGHLBass]'))+1]
        medium_ghl_bass = file_contents.decode()[file_contents.decode().find('[MediumGHLBass]'):file_contents.decode().find('}', file_contents.decode().find('[MediumGHLBass]'))+1]
        easy_ghl_bass = file_contents.decode()[file_contents.decode().find('[EasyGHLBass]'):file_contents.decode().find('}', file_contents.decode().find('[EasyGHLBass]'))+1]
        
        # GHLRhythm
        expert_ghl_rhythm = file_contents.decode()[file_contents.decode().find('[ExpertGHLRhythm]'):file_contents.decode().find('}', file_contents.decode().find('[ExpertGHLRhythm]'))+1]
        hard_ghl_rhythm = file_contents.decode()[file_contents.decode().find('[HardGHLRhythm]'):file_contents.decode().find('}', file_contents.decode().find('[HardGHLRhythm]'))+1]
        medium_ghl_rhythm = file_contents.decode()[file_contents.decode().find('[MediumGHLRhythm]'):file_contents.decode().find('}', file_contents.decode().find('[MediumGHLRhythm]'))+1]
        easy_ghl_rhythm = file_contents.decode()[file_contents.decode().find('[EasyGHLRhythm]'):file_contents.decode().find('}', file_contents.decode().find('[EasyGHLRhythm]'))+1]
        
        # GHLCoop
        expert_ghl_coop = file_contents.decode()[file_contents.decode().find('[ExpertGHLCoop]'):file_contents.decode().find('}', file_contents.decode().find('[ExpertGHLCoop]'))+1]
        hard_ghl_coop = file_contents.decode()[file_contents.decode().find('[HardGHLCoop]'):file_contents.decode().find('}', file_contents.decode().find('[HardGHLCoop]'))+1]
        medium_ghl_coop = file_contents.decode()[file_contents.decode().find('[MediumGHLCoop]'):file_contents.decode().find('}', file_contents.decode().find('[MediumGHLCoop]'))+1]
        easy_ghl_coop = file_contents.decode()[file_contents.decode().find('[EasyGHLCoop]'):file_contents.decode().find('}', file_contents.decode().find('[EasyGHLCoop]'))+1]
        
        GlobalText.single = expert_single + '\n' + hard_single + '\n' + medium_single + '\n' + easy_single + '\n'
        GlobalText.double_guitar = expert_double_guitar + '\n' + hard_double_guitar + '\n' + medium_double_guitar + '\n' + easy_double_guitar + '\n'
        GlobalText.double_bass = expert_double_bass + '\n' + hard_double_bass + '\n' + medium_double_bass + '\n' + easy_double_bass + '\n'
        GlobalText.double_rhythm = expert_double_rhythm + '\n' + hard_double_rhythm + '\n' + medium_double_rhythm + '\n' + easy_double_rhythm + '\n'
        GlobalText.keyboard = expert_keyboard + '\n' + hard_keyboard + '\n' + medium_keyboard + '\n' + easy_keyboard + '\n'
        GlobalText.drums = expert_drums + '\n' + hard_drums + '\n' + medium_drums + '\n' + easy_drums + '\n'
        
        GlobalText.ghl_guitar = expert_ghl_guitar + '\n' + hard_ghl_guitar + '\n' + medium_ghl_guitar + '\n' + easy_ghl_guitar + '\n'
        GlobalText.ghl_bass = expert_ghl_bass + '\n' + hard_ghl_bass + '\n' + medium_ghl_bass + '\n' + easy_ghl_bass + '\n'
        GlobalText.ghl_rhythm = expert_ghl_rhythm + '\n' + hard_ghl_rhythm + '\n' + medium_ghl_rhythm + '\n' + easy_ghl_rhythm + '\n'
        GlobalText.ghl_coop = expert_ghl_coop + '\n' + hard_ghl_coop + '\n' + medium_ghl_coop + '\n' + easy_ghl_coop + '\n'
        
    
    display = events_display.replace('\n  ', '\n')
    self.plainTextEdit.setPlainText(display.strip())