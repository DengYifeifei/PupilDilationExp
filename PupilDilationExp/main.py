from experiment import Experiment
from fire import Fire
import logging




def main(setting_number=None, name=None, test=False, fast=False, full=False, mouse=False, **kws):
    if test and name is None:
        name = 'test'
    # if fast:
    #     kws['block_length'] = 10
    exp = Experiment(setting_number, name, full_screen=(not test) or full, **kws)
    if test:
        #exp.welcome() 
        #exp.practice_intro()
        #exp.practice()
        #exp.setup_eyetracker(mouse)
        exp.intro_main()
        exp.main()
        exp.save_data()
        return
    else:
        try:
            if fast:
                exp.block_length = 3
                exp.n_block = 2
                #exp.welcome()
                #exp.practice_intro()
                #exp.practice(True)
                exp.setup_eyetracker()
                #exp.intro_main()
                exp.main()
            else:
                exp.practice_blocklen = 2 
                exp.block_length = 30
                #exp.welcome()
                exp.n_block = 3
                #exp.practice_intro()
                #exp.practice()
                #exp.intro_main()
                exp.setup_eyetracker()
                exp.main()
                exp.save_data(done=True)
            exp.save_data(done=True)
        except:
            if test:
                exit(1)
            logging.exception('Uncaught exception in main')
            exp.win.clearAutoDraw()
            exp.win.showMessage("Drat! The experiment has encountered an error.\nPlease inform the experimenter.")
            exp.win.flip()
            try:
                exp.save_data()
                raise
            except:
                logging.exception('error on second save data attempt')
                exp.emergency_save_data()
                raise


if __name__ == '__main__':
    Fire(main)

