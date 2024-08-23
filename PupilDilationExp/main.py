from experiment import Experiment
from fire import Fire
import logging


# def main(pid=None, name=None, test=False, setting_number = 0, fast=False, full=False, mouse=False, hotfix=False, skip_instruct=False, resume_block=None, **kws):
#     if test and name is None:
#         name = 'test'
#     # if fast:
#     #     kws['n_practice'] = 2
#     #     kws['n_block'] = 2
#     #     kws['block_duration'] = 15/60

#     if pid is None:
#         if test:
#             pid = 0
#         else:
#             pid = int(input("\n Please enter the participant ID number: "))

#     exp = Experiment(setting_number, pid, name, full_screen=(not test) or full, test_mode=bool(test), **kws)
#     if test == "save":
#         exp.save_data()
#         exit()
#     if test == "practice":
#         #exp.intro_main()
#         #exp.welcome()
#         exp.practice_intro()
#         exp.practice()
#         exit()
#     if test == "main":
#         if not mouse:
#             exp.setup_eyetracker()
#         exp.main()
#         exit()
#     # elif test == "practice":
#     #     exp.practice()
#     #     exp.intro_main()
#     #     exp.main()
#     else:
#         try:
#             if not (skip_instruct or resume_block):
#                 exp.welcome() 
#                 exp.practice_intro()
#                 exp.practice()
#                 exp.setup_eyetracker(mouse)
#                 exp.intro_main()

#             if resume_block:
#                 exp.message(
#                     f"Resuming experiment at Block {resume_block}.\n"
#                     "Note that the reported bonuses will not reflect the money you've already earned "
#                     "(but we still have that information!)",
#                     space=True
#                 )
#                 #random.shuffle(exp.trials['main'])
#                 #exp.main_trials = iter(exp.trials['main'])

#             exp.main(resume_block)
#             exp.save_data()
#         except:
#             if test:
#                 raise
#             logging.exception('Uncaught exception in main')
#             exp.win.clearAutoDraw()
#             exp.win.showMessage("Drat! The experiment has encountered an error.\nPlease inform the experimenter.")
#             exp.win.flip()
#             try:
#                 exp.save_data()
#                 raise
#             except:
#                 logging.exception('error on second save data attempt')
#                 exp.emergency_save_data()
#                 raise


# if __name__ == '__main__':
#     Fire(main)



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
                # exp.block_length = 
                exp.welcome()
                exp.practice_intro()
                exp.practice()
                exp.setup_eyetracker()
                exp.intro_main()
                exp.main()
                exp.save_data()
            exp.save_data()
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


# def main(pid=None, name=None, test=False, setting_number = 0, fast=False, full=False, mouse=False, hotfix=False, skip_instruct=False, resume_block=None, **kws):
#     if test and name is None:
#         name = 'test'
#     # if fast:
#     #     kws['n_practice'] = 2
#     #     kws['n_block'] = 2
#     #     kws['block_duration'] = 15/60

#     if pid is None:
#         if test:
#             pid = 0
#         else:
#             pid = int(input("\n Please enter the participant ID number: "))

#     exp = Experiment(setting_number, pid, name, full_screen=(not test) or full, test_mode=bool(test), **kws)
#     if test == "save":
#         exp.save_data()
#         exit()
#     if test == "practice":
#         #exp.intro_main()
#         #exp.welcome()
#         exp.practice_intro()
#         exp.practice()
#         exit()
#     if test == "main":
#         if not mouse:
#             exp.setup_eyetracker()
#         exp.main()
#         exit()
#     # elif test == "practice":
#     #     exp.practice()
#     #     exp.intro_main()
#     #     exp.main()
#     else:
#         try:
#             if not (skip_instruct or resume_block):
#                 exp.welcome() 
#                 exp.practice_intro()
#                 exp.practice()
#                 exp.setup_eyetracker(mouse)
#                 exp.intro_main()

#             if resume_block:
#                 exp.message(
#                     f"Resuming experiment at Block {resume_block}.\n"
#                     "Note that the reported bonuses will not reflect the money you've already earned "
#                     "(but we still have that information!)",
#                     space=True
#                 )
#                 #random.shuffle(exp.trials['main'])
#                 #exp.main_trials = iter(exp.trials['main'])

#             exp.main(resume_block)
#             exp.save_data()
#         except:
#             if test:
#                 raise
#             logging.exception('Uncaught exception in main')
#             exp.win.clearAutoDraw()
#             exp.win.showMessage("Drat! The experiment has encountered an error.\nPlease inform the experimenter.")
#             exp.win.flip()
#             try:
#                 exp.save_data()
#                 raise
#             except:
#                 logging.exception('error on second save data attempt')
#                 exp.emergency_save_data()
#                 raise


# if __name__ == '__main__':
#     Fire(main)