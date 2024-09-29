import re
import numpy as np
import pandas as pd
import math
import json 

class EyeLinkParser:
    def __init__(self, eye_folder, asc_encoding='ISO-8859-1'):
        self.eye_dirfolder = eye_folder
        # self.trial_dir = trial_dir
        self.asc_encoding = asc_encoding
        self.current_offset = np.nan
        self.rows = []  # Collect all rows in a list to append at once
        self.trial_index = 0
        #self.switch = 0
        #self.visit = 0
        self.event = None
        # self.wid = wid
        
    def import_trial_data(self, trial_dir):
        """ Imports trial data from a JSON file. """
        self.trial_dir = trial_dir
        with open(trial_dir, 'r') as file:
            return json.load(file)

    def parse_asc_file(self, path):
        """ Parses the ASC file for eye-tracking data. """
        with open(path, 'r', encoding=self.asc_encoding) as file:
            for index, line in enumerate(file):
                if 'MSG' in line:
                    self.parse_message(line)
                if 'SFIX' in line:
                    #self.parse_fixation_detail(line, index, path)
                    self.parse_fixation_detail(line, index, file)
                if 'EFIX' in line:
                    self.parse_fixation_summary(line)
                if re.match(r"^\d+\s+\d+\.\d+\s+\d+\.\d+", line):
                    self.parse_gaze(line)
                if 'EBLINK' in line:
                    self.parse_blink(line)
                if 'ESACC' in line:
                    self.parse_saccade(line)
        # Convert the collected rows to a DataFrame once all lines are processed
        self.data_frame = pd.DataFrame(self.rows)
        return self.data_frame



    def parse_message(self, line):
        """ Parses MSG lines for time events and handles offset calculations. """
        msg_match = re.search(r"MSG\s+(\d+)\s+.*\"time\":\s+(\d+\.\d+).*\"event\":\s+\"([^\"]+)\"", line)
        if msg_match:
            t_el, t_py, self.event = msg_match.groups()
            t_el, t_py = float(t_el), float(t_py)
            t_el /= 1000  # Convert to seconds
            offset = t_py - t_el
            #if np.isnan(self.current_offset) or "drift check" in self.event:
            self.current_offset = offset  # Update offset if the event is 'drift check' or first time
            #print("offset", offset)
            if self.event == 'initialize':
                self.trial_index += 1
                #
                if self.trial_index == 1:
                    print('offset at first', self.current_offset)
                    
                if self.trial_index == 30:
                    print('offset later', self.current_offset)
                    
                #self.visit = 0
                #self.switch = 0
            #if self.event == 'visit':
                #self.visit += 1
            #if self.event == 'switch':
                #self.switch =+1
            
            self.rows.append({
                'Type': 'Message',
                'Event': self.event,
                #'Visit': self.visit,
                #'Switch': self.switch,
                'Time': t_el,
                'TimeEvent': t_py,
                'Offset': offset - self.current_offset,
                'trial_index':self.trial_index
            })

    # def retrieve_block(self, file, start, end):
    #     for line in file:
    #         first_number = int(line.split()[0])
            
    #         # Start recording when the first number matches start_number
    #         if first_number == start_number:
    #             recording = True
            
    #         # Add line to the block if we're in the recording phase
    #         if recording:
    #             block.append(line.strip())
            
    #         # Stop recording when the first number matches end_number
    #         if first_number == end_number:
    #             break
    

        
    def parse_fixation_detail(self, line, index, file):
                            #self.parse_fixation(line, index, path)

        """ Parses fixation data from EFIX lines. """
        #print('parse fixation line', line)
        #print('path',path)
        fixation_match = re.search(r"SFIX\s+(L|R)\s+(\d+)", line)
        if fixation_match:
            for i, line in enumerate(file, start= index+1):
                pupilData_pattern = r"(\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+"
                pupilData_match = re.search(pupilData_pattern, line)
                if pupilData_match:
                    t_el, x, y, pupil = map(float, pupilData_match.groups())
                    t_el= float(t_el)
                    t_el /= 1000 
                    t_py = t_el + self.current_offset
                    self.rows.append({'Type': 'Fixation', 'Time': t_el, 'TimeEvent': t_py, 'X': x, 'Y': y, 'trial_index':self.trial_index, 'event':self.event, 'Pupil': pupil, 'trial_index':self.trial_index})
                else:
                    pupilSummary_match = re.search(r"EFIX\s+(L|R)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+)", line)
                    eye, start, end, duration, x, y, pupil = pupilSummary_match.groups()
                    start_, end_, duration_ = map(lambda x: float(x) / 1000, [start, end, duration])
                    x, y, pupil = map(float, [x, y, pupil])
                    start_ += self.current_offset
                    end_ += self.current_offset
                    self.rows.append({'Type': 'Fixation', 'Start': start_, 'End': end_, 'Duration': duration_, 'X': x, 'Y': y, 'Pupil': pupil, 'trial_index':self.trial_index, 'event':self.event})

        
                              
    def parse_gaze(self, line):
        """ Parses gaze data from lines that potentially contain gaze information. """
        gaze_match = re.search(r"(\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)", line)
        if gaze_match:
            t_el, x, y = map(float, gaze_match.groups())
            t_el /= 1000  # Convert to seconds
            t_py = t_el + self.current_offset
            #node = self.assign_node(x, y, self.node_positions)
            self.rows.append({'Type': 'Gaze', 'TimeEvent': t_py, 'X': x, 'Y': y, 'trial_index':self.trial_index, 'event':self.event})

    def parse_blink(self, line):
        """ Parses blink data from EBLINK lines. """
        blink_match = re.search(r"EBLINK\s+(\d+)\s+(\d+)\s+(\d+)", line)
        if blink_match:
            start, end, duration = map(lambda x: float(x) / 1000, blink_match.groups())
            start += self.current_offset
            end += self.current_offset
            self.rows.append({'Type': 'Blink', 'Start': start, 'End': end, 'Duration': duration, 'trial_index':self.trial_index, 'event':self.event})
    
    def parse_saccade(self, line):
        """
        Parses saccade data from ESACC lines.
        ESACC R 3216221 3216233 13 515.2 381.6 531.2 390.7 0.51 58
        """
        saccade_match = re.search(
            r"ESACC\s+(L|R)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+)", line)
        if saccade_match:
            eye, start, end, duration, start_x, start_y, end_x, end_y, amplitude, peak_velocity = saccade_match.groups()
            start, end, duration = map(lambda x: float(x) / 1000, [start, end, duration])  # Convert time to seconds
            start_x, start_y, end_x, end_y, amplitude, peak_velocity = map(float, [start_x, start_y, end_x, end_y, amplitude, peak_velocity])
            #start_node = self.assign_node(start_x, start_y, self.node_positions)
            #end_node = self.assign_node(end_x, end_y, self.node_positions)

            self.rows.append({
                'Type': 'Saccade',
                'Eye': eye,
                'Start': start,
                'End': end,
                'Duration': duration,
                'Start_X': start_x,
                'Start_Y': start_y,
                'End_X': end_x,
                'End_Y': end_y,
                'Amplitude': amplitude,
                'Peak_Velocity': peak_velocity,
                #'Start_Node': start_node,
                #'End_Node': end_node,
                'trial_index': self.trial_index,
                'event': self.event,
                # 'visit': self.visit,
                # 'switch': self.switch
            })
