from psychopy import core, visual, gui, data, event, sound
import numpy as np
import logging
import json
from eyetracking import height2pix
from util import jsonify
import random
from config import KEY_CONTINUE, LABEL_CONTINUE

wait = core.wait

from config import KEY_CONTINUE, KEY_ABORT, SOUND_PATH, KEYS_CORRECT

# TRIGGERS = {
#     'show description': 0,
#     'show graph': 1,
#     'start acting': 2,
#     'done': 3,
# }

TRIGGERS = {
    'show fixation': 0,
    'show cue': 1,
    'start sound': 2,
    'show feedback': 3,
    'done': 4,
}


class AbortKeyPressed(Exception): pass


class Trial(object):
    def __init__(self, win, pos=(0, 0), feedback = False, start_mode=None, 
                 feedback_duration=3, action_time=2,
                 eyelink=None, triggers=None, **kws):
        self.win = win
        
    
        for key, value in kws.items():
            setattr(self, key, value)

   
        self.pos = pos #eye position
        self.start_mode = start_mode or ('drift_check' if eyelink else 'space')

        
        self.fixation_duration = 0.5
        self.cue_duration = 1.5
        self.sound_duration = 1
        self.pre_trial_gap = random.uniform(1.5, 2.5)
        self.feedback_duration = feedback_duration
        self.feedback = feedback 
        self.action_time = action_time

        self.current_time = None
        self.start_time = None
        self.end_time = None

        self.eyelink = eyelink
        self.triggers = triggers
        self.recieved_response = None
        self.response_time = None

        self.status = 'ok'
        self.start_time = self.done_time = None
        #self.disable_click = False
        
        self.correct = 0 #self.score = 0
        self.rt = None
        #self.current_state = None
        self.fixated = None #在的时候有用calibration的时候有用
        self.fix_verified = None #后面没有用到
        self.data = {
            "trial": {
                'cue_direction': getattr(self, 'cue_direction', None), 
                'stimulus': getattr(self, 'stimulus', None), 
                'correct_response': getattr(self, 'correct_response', None),
                'left_cue_condition': getattr(self, 'left_cue_condition', None),
                'stimA_condition': getattr(self, 'stimA_condition', None)
            },
            "events": [], # fixation, cue, balabala       
        }
        # self.data = {
        #     "trial": {
        #         "kind": self.__class__.__name__,
        #         "graph": graph,
        #         "rewards": rewards,
        #         "reward_info": reward_info,
        #         "initial_stage": initial_stage,
        #         "hide_states": hide_states,
        #         "hide_rewards_while_acting": hide_rewards_while_acting,
        #         "hide_edges_while_acting": hide_edges_while_acting,

        #         "start": start,
        #     },
        #     "events": [],
        #     "flips": [],
        #     "mouse": [],
        # }
        logging.info("begin trial " + jsonify(self.data["trial"]))
        #self.gfx = Graphics(win)
        #self.mouse = event.Mouse()
        self.done = False
        

    def wait_keys(self, keys, time_limit=float('inf')):
        keys = event.waitKeys(maxWait=time_limit, keyList=[*keys, KEY_ABORT])
        if keys and KEY_ABORT in keys:
            self.status = 'abort'
            raise AbortKeyPressed()
        else:
            return keys


    def log(self, event, info={}):
        time = core.getTime()
        logging.debug(f'{self.__class__.__name__}.log {time:3.3f} {event} ' + ', '.join(f'{k} = {v}' for k, v in info.items()))
        datum = {
            'time': time,
            'event': event,
            **info
        }
        self.data["events"].append(datum)
        if self.triggers and event in TRIGGERS:
            self.triggers.send(TRIGGERS[event])
        if self.eyelink:
            self.eyelink.message(jsonify(datum), log=False)

    def tick(self):
        self.current_time = core.getTime()
        if self.end_time is not None: #TODO
            time_left = self.end_time - self.current_time
            if time_left > 0:
                p = time_left / (self.end_time - self.start_time)
                self.timer.setHeight(0.9 * p)
                if self.stage == 'acting' and time_left < 3:
                    p2 = time_left / 3
                    original = -.2 * np.ones(3)
                    red = np.array([1, -1, -1])
                    self.timer.setColor(p2 * original + (1-p2) * red)
        self.last_flip = t = self.win.flip()
        self.data["mouse"].append(self.mouse.getPos())
        self.data["flips"].append(t)
        return t
   

   

    def start_recording(self):
        self.log('start recording')
        self.eyelink.start_recording()
        # TODO: draw reference
        # left = int(scn_width/2.0) - 60
        # top = int(scn_height/2.0) - 60
        # right = int(scn_width/2.0) + 60
        # bottom = int(scn_height/2.0) + 60
        # draw_cmd = 'draw_filled_box %d %d %d %d 1' % (left, top, right, bottom)
        # el_tracker.sendCommand(draw_cmd)





        
    def fixation_cross(self, training_mode=False):
        
        fixation = visual.TextStim(self.win, "+", pos=self.pos, color='white', height=.05)
        
        
        if training_mode:
            fixation.autoDraw = True
            
        else:
            fixation.draw()
        
        self.log('show fixation')
        self.win.flip()
        
        return fixation


    def cue(self, training_mode = False):
        
        if self.cue_direction == 'left':
            sign = '<'
        elif self.cue_direction == 'right':
            sign = '>'
        cue = visual.TextStim(self.win, sign, pos=self.pos, color='white', height=.05)

        if training_mode:
            cue.autoDraw = True

        else:
            cue.draw()
        
        self.log('show cue')

        
        self.win.flip()

        return cue
    
    def sound(self):
        soundpath = SOUND_PATH[self.stimulus] # soundpaths 应该是一个dictionary self.stimulus 是key
        sound_stim = sound.Sound(soundpath, secs=self.sound_duration)

        self.log('start sound')
        sound_stim.play()

    def show_feedback(self, correct_response, received_response):
        if received_response: 
            if correct_response == received_response[0]:
                result = 'correct'
            else:
                result = 'incorrect'
        else:
            result = 'no response recieved'
        
        self.log('show feedback', info = {'content':result})
        
        visual.TextStim(self.win, result, pos=self.pos, color='white', height=.05, alignText='left', anchorHoriz='center').draw()
        visual.TextStim(self.win, f'press {LABEL_CONTINUE} to continue', pos=(0, -0.1), color='white', height=.025, alignText='left', anchorHoriz='center').draw()

        
        self.win.flip()
        event.waitKeys(keyList=['space', KEY_CONTINUE],maxWait = 10.0)
        self.win.flip()


        
        
    def run(self):#one_step=False, skip_planning=False
        # if self.start_mode == 'drift_check':
        #     self.log('begin drift_check')
        #     self.status = self.eyelink.drift_check(self.pos)
        # elif self.start_mode == 'fixation':
        #     self.log('begin fixation')
        #     self.status = self.eyelink.fake_drift_check(self.pos)
        # elif self.start_mode == 'space':
        #     self.log('begin space')
        #     visual.TextStim(self.win, f'press {KEY_CONTINUE.upper()} to start', pos=self.pos, color='white', height=.035).draw()
        #     self.win.flip()
        #     self.wait_keys(['space', KEY_CONTINUE])

        self.log('initialize', {'status': self.status}) 

        if self.status in ('abort', 'recalibrate'):
            self.log('done', {"status": self.status}) 
            return self.status

        if self.eyelink:
            self.start_recording()

        self.log('start')
        self.start_time = core.getTime()

        self.fixation_cross() 
        wait(self.pre_trial_gap)
        self.win.flip()

        self.cue()
        wait(1.5) #wait(self.cue_duration)
        self.win.flip()

        self.fixation_cross() 
        wait(self.fixation_duration)
        self.win.flip()

        #self.log('sound')
        #self.sound_start = core.getTime
        self.sound()
        sound_onset = core.getTime()
        
        wait(0.5)
        self.log('start decision window')
        self.recieved_response = self.wait_keys(KEYS_CORRECT, time_limit=3.0)

        if self.recieved_response:
            self.response_time = core.getTime()
            self.rt = self.response_time - sound_onset

            if self.recieved_response[0] == self.correct_response:
                self.correct = 1
                self.log('response', info = {'response':self.recieved_response[0],'performance':'Correct'})
            else:
                self.log('response', info = {'response':self.recieved_response[0],'performance':'Incorrect'})

        else:
            self.log('response', info = {'response':self.recieved_response,'performance':None})
        

        if self.feedback:    
            self.feedback_time = core.getTime()
            self.show_feedback(self.correct_response, self.recieved_response)

        self.log('done')
        self.done_time = core.getTime()
        logging.info("end trial " + jsonify(self.data["events"]))
    
        if self.eyelink:
            self.eyelink.stop_recording()
        
    
        #wait(self.pre_trial_gap)
        
        self.win.flip()

        return self.status #为什么要return
    
    # class CalibrationTrial(GraphTrial):
    #     """docstring for CalibrationTrial"""
    #     all_failures = np.zeros(11)  # across separate runs ASSUME graph doesn't change

    #     def __init__(self, *args, saccade_time=.7, n_success=2, n_fail=3, target_delay=.3 , **kwargs):
    #         kwargs['gaze_contingent'] = True
    #         kwargs['fixation_lag'] = .1
    #         kwargs['end_time'] = None

    #         self.saccade_time = saccade_time
    #         self.n_success = n_success
    #         self.n_fail = n_fail
    #         self.target_delay = target_delay

    #         self.target = None
    #         self.last_target = None
    #         self.arrow = None
    #         self.result = None

    #         super().__init__(*args, **kwargs)

    #     def node_label(self, i):
    #         return {
    #             # self.completed: ''
    #             # self.fixated: '',
    #             self.target: 'O',
    #         }.get(i, '')
        
    #     def do_timeout(self):
    #         self.log('timeout')
    #         logging.info('timeout')
    #         self.result = 'timeout'

    #     def draw_arrow(self):
    #         if self.arrow is not None:
    #             self.arrow.setAutoDraw(False)
    #         if self.last_target is not None:
    #             self.arrow = self.gfx.arrow(self.nodes[self.last_target], self.nodes[self.target])

    #     def new_target(self):
    #         initial = self.target is None
    #         self.last_target = self.target

    #         if initial:
    #             self.target = np.random.choice(len(self.successes))
    #         else:
    #             p = np.exp(
    #                 -5 * self.successes +
    #                 self.all_failures[:len(self.successes)]
    #             )
    #             p[self.target] = 0
    #             p /= (sum(p) or 1)  # prevent divide by 0
    #             self.target = np.random.choice(len(p), p=p)

    #         self.target_time = 'flip'  # updated to be next flip time
    #         self.draw_arrow()
    #         self.update_node_labels()
    #         self.log('new target', {"state": self.target})

    #     def tick(self):
    #         t = super().tick()
    #         if self.target_time == 'flip':
    #             self.target_time = t

    #     def run(self, timeout=15):
    #         assert self.eyelink
    #         # self.eyelink.drift_check(self.pos)
    #         self.start_recording()
    #         self.show()
    #         self.successes = np.zeros(len(self.nodes))
    #         self.failures = np.zeros(len(self.nodes))
    #         self.uncomplete = set(range(len(self.nodes)))
    #         self.new_target()
    #         self.start_time = self.tick()
    #         self.log('start', {'flip_time': self.start_time})

    #         self.win.mouseVisible = False

    #         self.target_time += 5  # extra time for first fixation
    #         while self.result is None:
    #             self.update_fixation()
    #             if 'x' in event.getKeys():  # cancel key
    #                 self.log('cancel')
    #                 self.result = 'cancelled'

    #             elif self.last_flip > self.target_time + self.saccade_time:  # timeout
    #                 self.log('timeout', {"state": self.target})
    #                 self.failures[self.target] += 1
    #                 self.all_failures[self.target] += 1

    #                 self.set_node_label(self.target, 'X')
    #                 lab = self.reward_labels[self.target]
    #                 for p in range(FRAME_RATE):
    #                     lab.setOpacity(1 - (p // 10) % 2)
    #                     self.tick()
    #                 wait(self.target_delay)
    #                 lab.setOpacity(1)

    #                 if sum(self.failures) == self.n_fail or self.failures[self.target] == 2:
    #                     self.result = 'failure'
    #                 else:
    #                     self.new_target()

    #             elif self.fixated == self.target:  # fixated within time
    #                 self.log('fixated target', {"state": self.target})
    #                 self.successes[self.target] += 1

    #                 lab = self.reward_labels[self.target]
    #                 for p in self.gfx.animate(6/60):
    #                     lab.setHeight(0.04 + p * 0.02)
    #                     self.tick()
    #                 for p in self.gfx.animate(12/60):
    #                     lab.setHeight(0.06 - p * 0.03)
    #                     lab.setOpacity(1-p)
    #                     self.tick()
    #                 wait(self.target_delay)
    #                 lab.setOpacity(1)
    #                 lab.setHeight(.03)

    #                 if self.successes[self.target] == self.n_success:
    #                     self.uncomplete.remove(self.target)
    #                 if self.uncomplete:
    #                     self.new_target()
    #                 else:
    #                     self.result = 'success'

    #             # if not self.done and self.end_time is not None and self.start_time + self.end_time < core.getTime():
    #             #     self.do_timeout()


    #             t = self.tick()

    #         self.log('done')
    #         self.eyelink.stop_recording()
    #         wait(.3)
    #         self.fade_out()
    #         self.win.mouseVisible = True

    #         return self.result
