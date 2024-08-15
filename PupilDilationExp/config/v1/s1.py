
setting = {
    "parameters": {
        "points_per_cent": 2,
        "time_limit": 5,
        "correct_responses": ['j', 'f'],
        #"condition_probabilities": left_cue_prob*([stimA_prob**2, stimA_prob*(1-stimA_prob), (1-stimA_prob)**2, (1-stimA_prob)*stimA_prob]*2),
        "combination_num": 8 
    },
    "trials": {
        "practice": [
            {'cue_direction': 'left', 'stimulus': 'A|B', 'correct_response': 'j'},
            {'cue_direction': 'left', 'stimulus': 'A|A', 'correct_response': 'j'},
            {'cue_direction': 'left', 'stimulus': 'A|B', 'correct_response': 'j'},
            {'cue_direction': 'left', 'stimulus': 'B|B', 'correct_response': 'f'},
            {'cue_direction': 'left', 'stimulus': 'B|A', 'correct_response': 'f'},
            {'cue_direction': 'right', 'stimulus': 'A|A', 'correct_response': 'j'},
            {'cue_direction': 'right', 'stimulus': 'A|B', 'correct_response': 'f'},
            {'cue_direction': 'right', 'stimulus': 'B|B', 'correct_response': 'f'},
            {'cue_direction': 'right', 'stimulus': 'B|A', 'correct_response': 'j'}
        ],    
        "main": [
            {'cue_direction': 'left', 'stimulus': 'A|A', 'correct_response': 'j'},
            {'cue_direction': 'left', 'stimulus': 'A|B', 'correct_response': 'j'},
            {'cue_direction': 'left', 'stimulus': 'B|B', 'correct_response': 'f'},
            {'cue_direction': 'left', 'stimulus': 'B|A', 'correct_response': 'f'},
            {'cue_direction': 'right', 'stimulus': 'A|A', 'correct_response': 'j'},
            {'cue_direction': 'right', 'stimulus': 'A|B', 'correct_response': 'f'},
            {'cue_direction': 'right', 'stimulus': 'B|B', 'correct_response': 'f'},
            {'cue_direction': 'right', 'stimulus': 'B|A', 'correct_response': 'j'}
        ]
    }
}
