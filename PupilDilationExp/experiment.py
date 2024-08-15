import os
import logging
import importlib.util
import json
import re
from datetime import datetime
import psychopy
from psychopy import core, visual, gui, data, event, sound
from psychopy.tools.filetools import fromFile, toFile
import numpy as np
import random

from time import sleep
from util import jsonify
from config import KEY_CONTINUE, LABEL_CONTINUE, SAME_SOUND_A, SAME_SOUND_B, DIFFERENT_SOUND, KEYS_CORRECT
from trial import Trial, AbortKeyPressed
from bonus import Bonus
from eyetracking import EyeLink, MouseLink

import subprocess
from copy import deepcopy
from config import VERSION

from triggers import Triggers  

import hackfix

DATA_PATH = f'data/exp/{VERSION}'
CONFIG_PATH = f'config/{VERSION}' 
LOG_PATH = 'log'
PSYCHO_LOG_PATH = 'psycho-log'
for p in (DATA_PATH, CONFIG_PATH, LOG_PATH, PSYCHO_LOG_PATH):
    os.makedirs(p, exist_ok=True)

def stage(f):
    def wrapper(self, *args, **kwargs):
        self.win.clearAutoDraw()
        logging.info('begin %s', f.__name__)
        try:
            f(self, *args, **kwargs)
        except:
            stage = f.__name__
            logging.exception(f"Caught exception in stage {stage}")
            if f.__name__ == "run_main":
                logging.warning('Continuing to save data...')
            else:
                self.win.clearAutoDraw()
                self.win.showMessage('The experiment ran into a problem! Press C to continue or Q to quit and save data')
                self.win.flip()
                keys = event.waitKeys(keyList=['c', 'q'])
                self.win.showMessage(None)
                if 'c' in keys:
                    logging.warning(f'Retrying {stage}')
                    wrapper(self, *args, **kwargs)
                else:
                    raise
        finally:
            self.win.clearAutoDraw()
            self.win.flip()

    return wrapper

# def get_next_config_number():
#     used = set()
#     for fn in os.listdir(DATA_PATH):
#         m = re.match(r'.*_P(\d+)\.', fn)
#         if m:
#             used.add(int(m.group(1)))

#     possible = range(0, 1 + len(os.listdir(CONFIG_PATH)))
#     try:
#         n = next(i for i in possible if i not in used)
#         return n
#     except StopIteration:
#         print("WARNING: USING RANDOM CONFIGURATION NUMBER")
#         return np.random.choice(list(possible))


def text_box(win, msg, pos, autoDraw=True, wrapWidth=.8, height=.035, alignText='left', **kwargs): 
    '''调整word wrap'''
    stim = visual.TextStim(win, msg, pos=pos, color='white', wrapWidth=wrapWidth, height=height, alignText=alignText, anchorHoriz='center', **kwargs)
    stim.autoDraw = autoDraw
    return stim
    import IPython, time; IPython.embed(); time.sleep(0.5)

class Experiment(object):
    def __init__(self, setting_number, block_length = 30, left_cue_conditions= None, stimA_conditions = None, name=None, full_screen=False, test_mode=False, **kws):
        if setting_number is None:
            setting_number = 0 
        self.setting_number = setting_number
        print('>>>', self.setting_number) #setting0: Ato'F' or setting1: Bto'F'

        self.full_screen = full_screen
        self.sound_len = 2.5 
        self.training_pass_boundry = 0.85

        timestamp = datetime.now().strftime('%y-%m-%d-%H%M')
        self.id = f'{timestamp}_setting{setting_number}'

        if name:
            self.id += '-' + str(name)

        self.setup_logging()
        logging.info('git SHA: ' + subprocess.getoutput('git rev-parse HEAD'))

        setting_file_name = f's{setting_number}'
        logging.info('setting file name: ' + setting_file_name)
        setting_path = os.path.join(CONFIG_PATH, f'{setting_file_name}.py')
        spec = importlib.util.spec_from_file_location(setting_file_name, setting_path)
        setting_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(setting_module)

        #setting_file = importlib.import_module(setting_file_name)
        setting = setting_module.setting
        self.trials = setting['trials']
        self.parameters = setting['parameters']
        self.parameters.update(kws)
        logging.info('parameters %s', self.parameters)

        if 'gaze_tolerance' not in self.parameters:
            self.parameters['gaze_tolerance'] = 1.5

        self.block_length = block_length

        self.win = self.setup_window()
        self.eyelink = MouseLink(self.win, self.id)  # use mouse by default
        self.win._heldDraw = []  # see hackfix
        self.bonus = Bonus(1, 0) #'''?'''
        self.total_score = 0
        self.disable_gaze_contingency = False
        default_conditions =  [0.3, 0.5, 0.9]

        self.left_cue_conditions = default_conditions
        self.stimA_conditions = stimA_conditions or default_conditions
        #print("left_cue_conditions:", self.left_cue_conditions)

        self.n_block = len(self.left_cue_conditions)* len(self.stimA_conditions)
        self.main_condition_pairs = [{'left_cue_condition': i, 'stimA_condition': j} for i in self.left_cue_conditions for j in self.stimA_conditions]
        self.main_conditions_sequence = self.main_condition_pairs.copy()  
        random.shuffle(self.main_conditions_sequence)  
        #print(self.main_conditions_sequence)

        
        self.stimA_conditions = stimA_conditions

        self._message = text_box(self.win, '', pos=(0, 0), autoDraw=True, height=.035)
        self._tip = text_box(self.win, '', pos=(0, -0.1), autoDraw=True, height=.025)
        self._top_message = text_box(self.win, '', pos=(0, 0.3), autoDraw=True, height=.035)

        self._practice_trials = iter(self.trials['practice'])
        print(next(self._practice_trials))
        #print('self._practice_trials', self._practice_trials)
        #self.main_trials = iter(self.trials['main'])
        self.practice_i = -1
        self.main_data = []
        self.practice_data = []
        self.parameters['triggers'] = self.triggers = Triggers(**({'port': 'dummy'} if test_mode else {'port': 'dummy'}))

    def get_practice_trial(self, repeat=False,**kws):
        if not repeat:
            self.practice_i += 1
        select = self.trials['practice'][self.practice_i]
        print('select:',select)
        
        prm = {
            'eyelink': self.eyelink,
            **self.parameters,
            # 'gaze_contingent': False,
            # 'time_limit': None,
            # 'pos': (.3, 0),
            #'start_mode': 'immediate',
            # 'space_start': False,
            # ** select
            **select, 
            **kws
        }
        trial = Trial(self.win, **prm) #gt = GraphTrial(self.win, **prm)
        self.practice_data.append(trial.data) #self.practice_data.append(gt.data)
        return trial 

###
    @property
    def n_trial(self):
        return len(self.trials['main'])

    def setup_logging(self):
        logFormatter = logging.Formatter("%(asctime)s [%(levelname)s]  %(message)s")
        rootLogger = logging.getLogger()
        rootLogger.setLevel('DEBUG')

        fileHandler = logging.FileHandler(f"{LOG_PATH}/{self.id}.log")
        fileHandler.setFormatter(logFormatter)
        rootLogger.addHandler(fileHandler)

        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        consoleHandler.setLevel('INFO')
        rootLogger.addHandler(consoleHandler)

        logging.info(f'starting up {self.id} at {core.getTime()}')

        psychopy.logging.LogFile(f"{PSYCHO_LOG_PATH}/{self.id}-psycho.log", level=logging.INFO, filemode='w')
        psychopy.logging.log(datetime.now().strftime('time is %Y-%m-%d %H:%M:%S,%f'), logging.INFO)


    def setup_window(self):
        size = (1350,750) if self.full_screen else (650,500)
        win = visual.Window(size, allowGUI=True, units='height', fullscr=self.full_screen)
        logging.info(f'Created window with size {win.size}')
        # framerate = win.getActualFrameRate(threshold=1, nMaxFrames=1000)
        # assert abs(framerate - 60) < 2
        win.flip()
        # win.callOnFlip(self.on_flip)
        return win

    def on_flip(self):
        if 'q' in event.getKeys():
            exit()
        # if 'f' in event.getKeys(): 
        '''为什么不用KEY_QUIT'''

        self.win.callOnFlip(self.on_flip)

    def hide_message(self):
        self._top_message.autoDraw = False
        self._message.autoDraw = False
        self._tip.autoDraw = False
        self.win.flip()

    # def show_message(self):
    #     self._message.autoDraw = True
    #     self._tip.autoDraw = True
    #     self._top_message.autoDraw = True

    def show_message(self, show_center=True, show_top=True, show_tip=True):
        if show_center:
            self._message.autoDraw = True
        if show_top:
            self._top_message.autoDraw = True
        if show_tip:
            self._tip.autoDraw = True
        self.win.flip()  # Update the screen after setting autoDraw
 

    def message(self, msg=None, tmsg=None, space=False, tip_text=None):
        logging.debug('message: %s (%s)', msg, tip_text)

        # Determine which messages to show
        show_center = msg is not None
        show_top = tmsg is not None
        show_tip = tip_text is not None or space

        self.show_message(show_center=show_center, show_top=show_top, show_tip=show_tip)

        if show_center:
            self._message.setText(msg)
        if show_top:
            self._top_message.setText(tmsg)
        if show_tip:
            self._tip.setText(tip_text if tip_text else f'press {LABEL_CONTINUE} to continue' if space else '')

        self.win.flip()

        if space:
            event.waitKeys(keyList=['space', KEY_CONTINUE])

    # def message(self, msg=None, tmsg=None, space=False, tip_text=None):
    #     logging.debug('message: %s (%s)', msg, tip_text)
    #     self.show_message()
    #     self._message.setText(msg)
    #     self._top_message.setText(tmsg)
    #     self._tip.setText(tip_text if tip_text else f'press {LABEL_CONTINUE} to continue' if space else '')
    #     self.win.flip()
    #     if space:
    #         event.waitKeys(keyList=['space', KEY_CONTINUE])

    @stage
    def welcome(self): 
        self.triggers.send(4)
        logging.info('start Welcome')
        self.message(msg="Welcome to the experiment!", space = True)
        self.hide_message()

        self.message(msg='During the test, you are going to receive a series of sound pairs coming from both the left and the right channels of your headset.', space = True)
        self.hide_message()

        self.message(msg='Sometimes, the sounds are different:')
        core.wait(1.0)
        sound.Sound(DIFFERENT_SOUND, secs=self.sound_len).play()
        event.waitKeys(keyList=['space', KEY_CONTINUE])
        self.hide_message()


        self.message(msg='Other times, they are the same.')
        core.wait(1.0)
        sound.Sound(SAME_SOUND_A, secs=self.sound_len).play()
        event.waitKeys(keyList=['space', KEY_CONTINUE])
        self.hide_message()

        self.message(msg="Before hearing each pair of sounds, you'll receive cues indicating the stimulus you should respond to. Each stimulus has a corresponding correct response.", space= True)
        self.hide_message()

        self.message(msg = "By the end of the experiment, your bonus points would be calculated depending on the NUMBER of correct responses you made and how QUICK you made these responses.", space = True)
        self.hide_message()
        
        self.message(msg = "Now Listen!")
        core.wait(1)
        sound.Sound(SAME_SOUND_A, secs=self.sound_len).play()
        self.hide_message()
        core.wait(1)
        self.message(msg="The correct response to this sound is 'f'.", tip_text= "Press 'f' to continue.")
        event.waitKeys(keyList=['f'])
        self.hide_message()

        self.message(msg = "And")
        core.wait(1)
        sound.Sound(SAME_SOUND_B, secs=self.sound_len).play()
        self.hide_message()
        core.wait(1)
        self.message(msg="The correct response to this sound is 'j'.", tip_text= "Press 'j' to continue.")
        event.waitKeys(keyList=['j'])


    @stage
    def practice_intro(self):
        #logging.info('start practice intro')
        self.message(msg="Great! These are all the basic rules! Next, you'll be presented with a few practice trials to help you better remember the correct responses to each stimulus and the experiment format.", space= True)
        self.hide_message()

        print('practice index:',self.practice_i)
        example_trial = self.get_practice_trial() 
        print('practice index:',self.practice_i)
        
        fixation = example_trial.fixation_cross(training_mode = True)
        core.wait(1)
        self.message(msg = None, tmsg= "The cross in the center of the screen indicates the ideal fixation point and the begining of a trial. ", space=True)
        fixation.setAutoDraw(False)
        self.hide_message()

        cue = example_trial.cue(training_mode = True)
        core.wait(1)
        self.message(tmsg= "Then you'll receive a cue. Here, it is a left sign, which tells you that you are expected to respond to the sound coming from the left channel. Now please pay attention to the right channel!",
                            space=True)
        cue.setAutoDraw(False)
        self.win.flip()

        example_trial.sound()
        core.wait(0.5)
        self.message(tmsg= "Now please make the response",
                            space=False)
        logging.info('start decision window')
        example_trial.recieved_response = event.waitKeys(keyList=KEYS_CORRECT, maxWait=10.0)

        if example_trial.recieved_response:
            example_trial.response_time = core.getTime()

            if example_trial.recieved_response[0] == example_trial.correct_response:
                example_trial.correct = 1
                example_trial.log('response', info = {'response':example_trial.recieved_response[0],'performance':'Correct'})
                logging.info('recieved correct response')
            else:
                example_trial.correct = 0 
                example_trial.log('response', info = {'response':example_trial.recieved_response[0],'performance':'Incorrect'})
                logging.info('recieved incorrect response')
        else:
            example_trial.correct = 0
            example_trial.response_time = None
            example_trial.log('response', info = {'response':example_trial.recieved_response,'performance':None})
            logging.info('recieved no response')
        
        self.hide_message()

        example_trial.feedback_time = core.getTime()
        example_trial.show_feedback(example_trial.correct_response, example_trial.recieved_response)

        
        self.message(msg= f"Now you know the rules. You'll be able to pass the training session if you get {self.training_pass_boundry} of the {self.parameters['combination_num']} trials right. Ready? Let's begin!", space =True)
        self.hide_message()


    @stage
    def practice(self,fast=False):
        if fast:
            practice_blocklen = 2
        else:
            practice_blocklen = self.parameters["combination_num"]
        logging.info('start practice trials')
        failed_times = 0
        correct_proportion = 0 
        while correct_proportion < self.training_pass_boundry:
            self.practice_i = 1
            correct_count = 0
            for i in range(practice_blocklen - self.practice_i):
                self.message(msg = f'complete {practice_blocklen - i} practice rounds to continue',
                            space=True)
                self.hide_message()
                trial = self.get_practice_trial(feedback = True)
                trial.run()
                if trial.correct_response == 1:
                    correct_count += 1
            correct_proportion = correct_count/practice_blocklen
            if correct_proportion >= self.training_pass_boundry:
                self.message(msg="Great job!", space= True)
                self.hide_message()
            else:
                logging.info('retry practice trials')
                failed_times += 1
                if failed_times > 3: 
                    self.message(msg = "The experiment ran into a problem! Please tell the experimenter.")
                else: 
                    self.message(msg = "Let's try another round to familiar youself better with the stimuli!", space = True)
                    self.hide_message()
               

    @stage
    def setup_eyetracker(self, mouse=False):
        self.message(msg="Now we're going to calibrate the eyetracker. When you see a black "
                      "circle, look at it and hold your gaze steady", tip_text="wait for the experimenter")
        event.waitKeys(keyList=['space', 'c'])
        self.hide_message()
        if not mouse:
            self.eyelink = EyeLink(self.win, self.id)
        self.eyelink.setup_calibration()
        self.eyelink.calibrate()


    def generate_block_label(self, left_cue_prob= 0.3, stimA_prob = 0.7):
        num_left = int(10 * left_cue_prob)
        num_right = 10 - num_left

        num_o = int(10 * stimA_prob)
        num_x = 10 - num_o
        block_label = '<' * num_left + '>' * num_right + ' ' + 'o' * num_o + 'x' * num_x

        return block_label

    def center_message(self, msg, space=True):
        visual.TextStim(self.win, msg, color='white', wrapWidth=.8, alignText='center', height=.035).draw()
        self.win.flip()
        if space:
            event.waitKeys(keyList=[KEY_CONTINUE])   


    @stage
    def intro_main(self):
        self.message(msg= "Alright! We're ready to begin the main phase of the experiment.", space=True)
        self.hide_message()

        self.message(msg = f"There will be {self.n_block} blocks. Each block inludes 30 trials , taking 4 minites maximum.", space=True)
        self.hide_message()

        self.message(msg= "The blocks are all slightly different, because we changes the chances of showing a specific cue and sound stimulus between blocks. We will let you know the chances before starting each block. " 
                     , space= True)
        self.hide_message()
        
        example_lable = self.generate_block_label()
        self.message(msg = "For example, you may see a pattern as below. The left part indicates how often you will see a specific cue and the right part indicates how often you'll see a specific stimuli.", tip_text=example_lable)
        self.hide_message()

        self.message(msg = "Apart from that, it will be greatly appreciated if you can focus on the center of the screen as much as possible, since it will help us get better measurements :)", space= True)
        self.hide_message()

        self.message(msg= "Ready? Let go!", space= True)
        self.hide_message()



    def determine_cue(self, left_cue_probability):
        if not 0 <= left_cue_probability <= 1:
            raise ValueError("The probability must be between 0 and 1 inclusive.")
        
        cues = ['left', 'right']
        probabilities = [left_cue_probability, 1 - left_cue_probability]
        
        chosen_cue = np.random.choice(cues, p=probabilities)
        
        return chosen_cue 
    
    def determine_trial_stimuli(self, A_probability):
        if not 0 <= A_probability <= 1:
            raise ValueError("The probability must be between 0 and 1 inclusive.")
        
        stimuli = ['A|A', 'A|B', 'B|B', 'B|A']
        
        prob_AA = A_probability * A_probability
        prob_AB = A_probability * (1 - A_probability)
        prob_BB = (1 - A_probability) * (1 - A_probability)
        prob_BA = (1 - A_probability) * A_probability
        
        probabilities = [prob_AA, prob_AB, prob_BB, prob_BA]
        
        chosen_stimulus = np.random.choice(stimuli, p=probabilities)
        
        return chosen_stimulus

    def generate_trialstim(self, left_cue_probability, A_probability):
        cue_direction = self.determine_cue(left_cue_probability)
        stimulus = self.determine_trial_stimuli(A_probability)
        
        # Define the list of possible outcomes
        responses = self.trials['main']
        
        # Find the matching response
        for response in responses:
            if response['cue_direction'] == cue_direction and response['stimulus'] == stimulus:
                return response
        
        return None



    def run_test_trial(self, left_cue_probability, A_probability):
        trial = self.generate_trialstim(left_cue_probability, A_probability)
        prm = {**self.parameters, **trial}
        trial = Trial(self.win, **prm, eyelink=self.eyelink)
        trial.run() 
        psychopy.logging.flush()
        self.main_data.append(trial.data)

        logging.info('gt.status is %s', trial.status)
        self.bonus.add_points(trial.correct)  # bonus class 
        logging.info('current bonus: %s', self.bonus.dollars())
        # self.total_score += int(trial.score)

        return core.getTime() - trial.start_time

    @stage
    def main(self, resume_block=None):

        # iterating through blocks 
        start = 0 if resume_block is None else resume_block - 1

        for i in range(start, len(self.main_conditions_sequence)):
            
            left_cue_probability = self.main_conditions_sequence[i]['left_cue_condition']
            A_probability = self.main_conditions_sequence[i]['stimA_condition']
            logging.info(f"Starting block {i}: {self.main_conditions_sequence[i]}")
            block_notice = f"Starting block {i}: {self.main_conditions_sequence[i]}"
            block_label = self.generate_block_label(left_cue_prob=left_cue_probability, stimA_prob=A_probability)
            self.message(msg=block_notice, tip_text=block_label)
            self.hide_message()

            trial_count = 0
            print(trial_count, self.block_length)

            while trial_count < self.block_length: 
                try:
                    trial_count += 1
                    print(trial_count)
                    self.run_test_trial(left_cue_probability, A_probability)
                    logging.info('%d/%d', trial_count, self.block_length)

                except Exception as e:
                    if isinstance(e, AbortKeyPressed):
                        logging.warning("Abort key pressed")
                        msg = 'Abort key pressed!'
                    else:
                        logging.exception(f"Caught exception in main")
                        msg = 'The experiment ran into a problem! Please tell the experimenter.'

                    self.win.clearAutoDraw()
                    self.win.showMessage(msg + '\n' + 'Press C to continue, R to recalibrate, or Q to terminate the experiment and save data')
                    self.win.flip()
                    keys = event.waitKeys(keyList=['c', 'r', 'q'])
                    self.win.showMessage(None)
                    if 'c' in keys:
                        continue
                    elif 'r' in keys:
                        self.eyelink.calibrate()
                    else:
                        raise

            # end while
            # block summary
            if i < self.n_block - 1:
                self.center_message(f"You've completed block {i + 1} of {self.n_block}.\n{self.bonus.report_bonus()}.\n\n"
                    "Take a short break. Then let the experimenter know when you're ready to continue.", space=False)
                event.waitKeys(keyList=['space', 'c'])
                self.eyelink.calibrate()


    @property
    def all_data(self):
        return {
            'config_number': self.setting_number,
            'parameters': self.parameters,
            'main_data': self.main_data,
            'practice_data': self.practice_data,
            'window': self.win.size,
            'bonus': self.bonus.dollars()
        }

    @stage
    def save_data(self):
        self.message(f"You're done! {self.bonus.report_bonus('final')}",
                     tip_text="give us a few seconds to save the data", space=False)
        psychopy.logging.flush()

        fp = f'{DATA_PATH}/{self.id}.json'
        with open(fp, 'w') as f:
            f.write(jsonify(self.all_data))
        logging.info('wrote %s', fp)

        if self.eyelink:
            self.eyelink.save_data()

        self.message(f"You're done! {self.bonus.report_bonus('final')}",
                     tip_text="data saved! press Button 1 to exit", space=True)
        print("\n\nFINAL BONUS: ", self.bonus.dollars())

    def emergency_save_data(self):
        logging.warning('emergency save data')
        if self.eyelink:
            self.eyelink.save_data()
        logging.warning('eyelink data saved?')
        fp = f'{DATA_PATH}/{self.id}.txt'
        with open(fp, 'w') as f:
            f.write(str(self.all_data))
        logging.info('wrote %s', fp)



