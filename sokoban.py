
import subprocess
import os
import re
import tkinter as tk
class sokoban_smv_generator():
    def __init__(self, input_board):
        self.input_board = input_board.strip().splitlines()
        self.board = []  # 0s and 1s for floor and walls
        self.player = []  # [x, y] position of the player
        self.boxes = []  # List of [x, y] positions for boxes
        self.goals = []  # List of [x, y] positions for goals
        self.gen_board()
        self.N = len(self.board)
        self.M = len(self.board[0]) if self.board else 0  # Ensure correct width after gen_board
        self.res = "MODULE main\n"

    def gen_board(self):
        for y, row in enumerate(self.input_board):
            board_row = []
            for x, char in enumerate(row):
                if char == '#':
                    board_row.append(1)
                elif char == '-':
                    board_row.append(0)  # Explicit floor handling
                elif char == '.' or char == '*' or char == '+':
                    board_row.append(0)  # Goal, but treated as floor for this purpose
                    self.goals.append([x, y])
                else:
                    board_row.append(0)  # Treat all other characters as floor by default

                if char == '@'  or char == '+':
                    self.player = [x, y]
                elif char == '$' or char == '*':
                    self.boxes.append([x, y])
                
            self.board.append(board_row)

    def DEFINE_gen(self):
      self.res += "DEFINE\n"
      self.res += "  -- 1 represents wall, 0 represents an empty tile\n"
      self.res += "  grid := " + str(self.board).replace('[', '[').replace(']', ']') + ";\n"
      self.res += "  N := " + str(self.N) + ";\n"
      self.res += "  M := " + str(self.M) + ";\n"

      for index, goal in enumerate(self.goals):
          self.res += f"  i_box_goal{index+1} := {goal[1]};\n"  # j index is now i in SMV (column to row)
          self.res += f"  j_box_goal{index+1} := {goal[0]};\n"  # i index is now j in SMV (row to column)

    def VAR_gen(self):
        self.res += "VAR\n"
        self.res += f"  i_person : 0..{self.N-1};\n"
        self.res += f"  j_person : 0..{self.M-1};\n"

        # Generate variable definitions for each box
        for i in range(len(self.boxes)):
            self.res += f"  i_box{i+1} : 0..{self.N-1};\n"
            self.res += f"  j_box{i+1} : 0..{self.M-1};\n"

        self.res += "  action_person : {no-action, up, down, left, right};\n"
        self.res += "  boxes_overlap : boolean;\n"
        self.res += "  box_on_wall : boolean;\n"
        self.res += "  man_on_box : boolean;\n"
        self.res += "  man_on_wall : boolean;\n"

    def ASSIGN_gen(self):
        self.res += "ASSIGN\n"
        # Initialize player and box positions
        self.res += f"  init(i_person) := {self.player[1]};\n"
        self.res += f"  init(j_person) := {self.player[0]};\n"

        for i, box in enumerate(self.boxes):
            self.res += f"  init(i_box{i+1}) := {box[1]};\n"
            self.res += f"  init(j_box{i+1}) := {box[0]};\n"

        self.res += "  init(action_person) := {no-action};\n"
        self.res += "  init(boxes_overlap) := FALSE;\n"
        self.res += "  init(box_on_wall) := FALSE;\n"
        self.res += "  init(man_on_box) := FALSE;\n"
        self.res += "  init(man_on_wall) := FALSE;\n"

        # Define next states for man_on_wall
        self.res += "  next(man_on_wall) := case\n"
        self.res += f"    grid[i_person][j_person] = 1 : TRUE;\n"
        self.res += "    TRUE : FALSE;\n"
        self.res += "  esac;\n"

        # Define next states for man_on_box
        self.res += "  next(man_on_box) := case\n"
        for i in range(len(self.boxes)):
            self.res += f"    (i_person = i_box{i+1}) & (j_person = j_box{i+1}) : TRUE;\n"
        self.res += "    TRUE : FALSE;\n"
        self.res += "  esac;\n"

        # Define next states for box_on_wall
        self.res += "  next(box_on_wall) := case\n"
        for i in range(len(self.boxes)):
            self.res += f"    grid[i_box{i+1}][j_box{i+1}] = 1 : TRUE;\n"
        self.res += "    TRUE : FALSE;\n"
        self.res += "  esac;\n"

        # Define next states for boxes_overlap
        self.res += "  next(boxes_overlap) := case\n"
        for i in range(len(self.boxes)):
            for j in range(i + 1, len(self.boxes)):
                self.res += f"    (i_box{i+1} = i_box{j+1}) & (j_box{i+1} = j_box{j+1}) : TRUE;\n"
        self.res += "    TRUE : FALSE;\n"
        self.res += "  esac;\n"

        # Define next states for action_person considering walls
        self.res += "  next(action_person) := case\n"
        self.res += "    boxes_overlap : {no-action};\n"
        self.res += "    box_on_wall : {no-action};\n"
        self.res += "    man_on_box : {no-action};\n"
        self.res += "    man_on_wall : {no-action};\n"

        # Generate dynamic actions based on the player's position and nearby walls
        for i in range(self.N):
            for j in range(self.M):
                actions = []
                if self.board[i][j] == 0:  # Only consider actions if the current cell is not a wall
                    if i > 0 and self.board[i-1][j] == 0:  # Up
                        actions.append("up")
                    if i < self.N - 1 and self.board[i+1][j] == 0:  # Down
                        actions.append("down")
                    if j > 0 and self.board[i][j-1] == 0:  # Left
                        actions.append("left")
                    if j < self.M - 1 and self.board[i][j+1] == 0:  # Right
                        actions.append("right")

                # Add actions for this specific position
                if actions:
                    self.res += f"    (i_person = {i}) & (j_person = {j}) : {{{', '.join(actions)}}};\n"

        self.res += "    TRUE : {no-action};\n"  # Default case if no other conditions match
        self.res += "  esac;\n"
        for i in range(len(self.boxes)):
            # Next state for box i along the x-axis
            self.res += f"  next(i_box{i+1}) := case\n"
            self.res += f"    (next(action_person) = down) & (i_box{i+1} = i_person + 1) & (j_box{i+1} = j_person) & (i_box{i+1} + 1 < N) : i_box{i+1} + 1;\n"
            self.res += f"    (next(action_person) = up) & (i_box{i+1} = i_person - 1) & (j_box{i+1} = j_person) & (i_box{i+1} - 1 >= 0) : i_box{i+1} - 1;\n"
            self.res += f"    TRUE : i_box{i+1};\n"
            self.res += f"  esac;\n"

            # Next state for box i along the y-axis
            self.res += f"  next(j_box{i+1}) := case\n"
            self.res += f"     (next(action_person) = right) & (i_box{i+1} = i_person) & (j_box{i+1} = j_person + 1) & (j_box{i+1} + 1 < M) : j_box{i+1} + 1;\n"
            self.res += f"    (next(action_person) = left) & (i_box{i+1} = i_person) & (j_box{i+1} = j_person - 1) & (j_box{i+1} - 1 >= 0) : j_box{i+1} - 1;\n"
            self.res += f"    TRUE : j_box{i+1};\n"
            self.res += f"  esac;\n"

        # Define next states for moving the player
        self.res += "  next(i_person) := case\n"
        self.res += "    (next(action_person) = down) & (i_person + 1 < N) : i_person + 1;\n"
        self.res += "    (next(action_person) = up) & (i_person - 1 >= 0) : i_person - 1;\n"
        self.res += "    TRUE : i_person;\n"
        self.res += "  esac;\n"

        self.res += "  next(j_person) := case\n"
        self.res += "    (next(action_person) = right) & (j_person + 1 < M) : j_person + 1;\n"
        self.res += "    (next(action_person) = left) & (j_person - 1 >= 0) : j_person - 1;\n"
        self.res += "    TRUE : j_person;\n"
        self.res += "  esac;\n"


    def SPEC_gen(self, num_boxes):
        import itertools
        self.res += "LTLSPEC "

        # Generate all subsets of goal indices with the size num_boxes
        goal_subsets = list(itertools.combinations(range(len(self.goals)), num_boxes))

        # Generate all permutations of the goals
        goal_permutations = list(itertools.permutations(self.goals, num_boxes))

        spec_conditions = []
        for subset in goal_subsets:
            condition_groups = []
            for perm in goal_permutations:
                conditions = []
                for i, goal in enumerate(perm):
                    # goal[1] is the row index and goal[0] is the column index for the SMV specification
                    conditions.append(f"(i_box{subset[i]+1} = {goal[1]}) & (j_box{subset[i]+1} = {goal[0]})")
                condition_groups.append("(" + " & ".join(conditions) + ")")
            spec_conditions.append(" | ".join(condition_groups))

        spec_condition = " | ".join(spec_conditions)
        self.res += f"G!((!next(man_on_box) & !next(man_on_wall) & !next(box_on_wall) & !next(boxes_overlap)) & {spec_condition});\n"
    def generate_and_get_board(self,NumOfBoxes):
        # Run code generation methods
        self.DEFINE_gen()
        self.VAR_gen()
        self.ASSIGN_gen()
        self.SPEC_gen(NumOfBoxes)
        return self.res
def run_nuxmv(model_filename):
    commands = f""" 
read_model -i {model_filename}
go_bmc
check_ltlspec_bmc -k 30
"""
    # Start nuXmv in interactive mode and send commands
    nuxmv_process = subprocess.Popen(['nuXmv', '-int'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, errors = nuxmv_process.communicate(input=commands)

    # Extract the output of the last command only
    output_lines = output.strip().split('\n')
    last_command_output = []
    for line in reversed(output_lines):
        if line.startswith('-- specification'):
            break
        last_command_output.append(line)
    last_command_output.reverse()
    last_command_output = '\n'.join(last_command_output)

    output_filename = model_filename.split(".")[0] + ".out"
    with open(output_filename, "w") as f:
        f.write(last_command_output)

    print(f"Output saved to {output_filename}")

    LURD = result_to_LURD(output_filename)
    if len(LURD) > 2:
        LURD = LURD[:-2]
    with open(output_filename, "a") as f:
        f.write(f"results in lurd format : {LURD} \n")

    return output_filename, LURD  



def run_nuxmv_old(model_filename):
    commands = f""" 
read_model -i {model_filename}
go_bmc
check_ltlspec_bmc
"""
    # Run the command
    nuxmv_process = subprocess.Popen(["nuXmv", model_filename], stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
    output_filename = model_filename.split(".")[0] + ".out"

    stdout, _ = nuxmv_process.communicate()

    # Save output to file
    with open(output_filename, "w") as f:
        f.write(stdout)

    print(f"Output saved to {output_filename}")

    LURD = result_to_LURD(output_filename)
    if len(LURD)>2:
        LURD = LURD[:-2]
    with open(output_filename, "a") as f:
        f.write(f"results in lurd format : {LURD} \n")

    return output_filename,LURD


def generate_model_file(model_string,iteration):
    model_filename = f"result_model_for_iteration_{iteration}.smv"
    with open(model_filename, "w") as f:
        f.write(model_string)
    return model_filename

def results_runtime_SAT(model_filename): 
    # Define the sequence of commands to run in nuXmv
    commands = f""" 
read_model -i {model_filename}
go_bmc
check_ltlspec_bmc -k 40
time
"""

    # Start nuXmv in interactive mode and send commands
    process = subprocess.Popen(['nuXmv', '-int'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, errors = process.communicate(input=commands)
    output_lines = output.strip().split('\n')
    last_command_output = []
    for line in reversed(output_lines):
        if line.startswith('-- specification'):
            break
        last_command_output.append(line)
    last_command_output.reverse()
    last_command_output = '\n'.join(last_command_output)
    
    
    # Define the output filename
    output_filename = "output_sat.out"

    # Save the output after check_ltlspec_bmc to the output file
    with open(output_filename, "w") as f:
        f.write(last_command_output)

    # Regex to find the final elapsed time and total time after check_ltlspec_bmc
    time_pattern = r"elapse: (\d+\.\d+) seconds, total: (\d+\.\d+) seconds"
    time_match = re.search(time_pattern, output)
    
    # Regex to find the last checked bound
    bound_pattern = r"-- no counterexample found with bound (\d+)"
    bound_matches = re.findall(bound_pattern, output)
    final_bound = bound_matches[-1] if bound_matches else 'unknown'

    # Extract the elapsed and total time if available
    if time_match:
        elapsed_time = time_match.group(1)
        total_time = time_match.group(2)
    else:
        elapsed_time = 'unknown'
        total_time = 'unknown'

    # Compile results into a result string
    result_string = f"Runtime after check_ltlspec_bmc -k 30: {elapsed_time} seconds (Total time: {total_time} seconds)\nLast checked bound: {final_bound}"
    
    return result_string, output_filename

def results_runtime_SATold(model_filename): # sets SAT-solver engine
    # Define the sequence of commands to run in nuXmv
    commands = f""" 
read_model -i {model_filename}
go_bmc
check_ltlspec_bmc -k 30
time
"""

    # Start nuXmv in interactive mode and send commands
    process = subprocess.Popen(['nuXmv', '-int'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, errors = process.communicate(input=commands)

    # Optionally print outputs for debugging
    #print("Output:\n", output)
    #print("Errors:\n", errors)

    # Regex to find the final elapsed time and total time after check_ltlspec_bmc
    time_pattern = r"elapse: (\d+\.\d+) seconds, total: (\d+\.\d+) seconds"
    time_match = re.search(time_pattern, output)
    
    # Regex to find the last checked bound
    bound_pattern = r"-- no counterexample found with bound (\d+)"
    bound_matches = re.findall(bound_pattern, output)
    final_bound = bound_matches[-1] if bound_matches else 'unknown'

    # Extract the elapsed and total time if available
    if time_match:
        elapsed_time = time_match.group(1)
        total_time = time_match.group(2)
    else:
        elapsed_time = 'unknown'
        total_time = 'unknown'

    # Compile results into a result string
    result_string = f"Runtime after check_ltlspec_bmc -k 30: {elapsed_time} seconds (Total time: {total_time} seconds)\nLast checked bound: {final_bound}"
    return result_string

def results_runtime_BDD(model_filename): # sets BDD engine
    # Define the sequence of commands to run in nuXmv
    commands = f""" 
read_model -i {model_filename}
go
check_ltlspec
time
"""

    # Start nuXmv in interactive mode and send commands
    process = subprocess.Popen(['nuXmv', '-int'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, errors = process.communicate(input=commands)

    # Optionally print outputs for debugging
    #print("Output:\n", output)
    #print("Errors:\n", errors)

    # Regex to find the final elapsed time and total time after check_ltlspec_bmc
    time_pattern = r"elapse: (\d+\.\d+) seconds, total: (\d+\.\d+) seconds"
    time_match = re.search(time_pattern, output)

    # Extract the elapsed and total time if available
    if time_match:
        elapsed_time = time_match.group(1)
        total_time = time_match.group(2)
    else:
        elapsed_time = 'unknown'
        total_time = 'unknown'

    # Compile results into a result string
    result_string = f"Runtime after check_ltlspec: {elapsed_time} seconds (Total time: {total_time} seconds)\n"
    return result_string

#def results_runtime_BDD_STEPS(model_filename):
#    return "template string BDD STEPS"
#def results_runtime_SAT(model_filename):
#    return "template string SAT"    

def generate_result_file(model_filename ,iteration , check_bdd):
    runtime_BDD = "check bdd to generate bdd results"
    if check_bdd == "Yes":
        runtime_BDD = results_runtime_BDD(model_filename)
    runtime_SAT,output_filename = results_runtime_SAT(model_filename)
    LURD = result_to_LURD(output_filename)
    #if len(LURD)>2:
    #   LURD = LURD[:-2]
 
    #runtime_BDD_STEPS = results_runtime_BDD_STEPS(model_filename)
    #runtime_SAT = results_runtime_SAT(model_filename)
    results_filename = f"results_for_model_iteration_{iteration}.out"
    with open(results_filename,"w") as f:
        
        f.write(f"results in lurd format : {LURD} \n")
        f.write(f"""runtime results SAT:\n
        {runtime_SAT}\n
        runtime results BDD:\n
        {runtime_BDD}\n
        """)
    return LURD
        
def result_to_LURD(output_filename):
    # Open the file containing the nuXmv output
    with open(output_filename, 'r') as file:
        lines = file.readlines()
    
    # Variable to store the final sequence of actions
    lurd_sequence = []
    
    # Variables to keep track of the last action and its continuation
    last_action = None
    action_count = 0

    # Loop through each line in the file
    for line in lines:
        if "action_person" in line:
            action = line.split('=')[-1].strip()
            
            # Map the action string to the corresponding direction character
            if action == "left":
                action = 'L'
            elif action == "right":
                action = 'R'
            elif action == "up":
                action = 'U'
            elif action == "down":
                action = 'D'
            else:
                action = None  # For 'no-action' or unrecognized actions
            
            if last_action and action != last_action:
                # Append the accumulated action sequence
                lurd_sequence.append(last_action * action_count)
                # Reset the count for the new action
                action_count = 0
            
            # Update the last action seen
            last_action = action
        
        if "-> State:" in line:
            if last_action:
                # Count continuity of the same action until a change occurs
                action_count += 1

    # Handle the last sequence after the loop ends
    if last_action and action_count:
        lurd_sequence.append(last_action * action_count)
    
    # Join all actions into a single string
    return ''.join(lurd_sequence)

    
    
    
class Sokoban_mover:
    SYMBOLS = {
        '@': 'warehouse keeper',
        '+': 'warehouse keeper on goal',
        '$': 'box',
        '*': 'box on goal',
        '#': 'wall',
        '.': 'goal',
        '-': 'floor'
    }

    def __init__(self, board_str):
        self.board = [list(row) for row in board_str.strip().split('\n')]
        self.rows = len(self.board)
        self.cols = len(self.board[0])
        self.keeper_pos = self.find_keeper()

    def find_keeper(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] == '@' or self.board[r][c] == '+':
                    return (r, c)
        return None

    def move(self, direction):
        dr, dc = 0, 0
        if direction == 'L':
            dc = -1
        elif direction == 'R':
            dc = 1
        elif direction == 'U':
            dr = -1
        elif direction == 'D':
            dr = 1

        r, c = self.keeper_pos
        nr, nc = r + dr, c + dc
        nnr, nnc = r + 2 * dr, c + 2 * dc

        if self.is_valid_move(nr, nc, nnr, nnc):
            self.update_board(r, c, nr, nc, nnr, nnc)

    def is_valid_move(self, nr, nc, nnr, nnc):
        if self.board[nr][nc] in ('-', '.'):
            return True
        elif self.board[nr][nc] in ('$', '*') and self.board[nnr][nnc] in ('-', '.'):
            return True
        return False

    def update_board(self, r, c, nr, nc, nnr, nnc):
        if self.board[nr][nc] in ('-', '.'):
            self.board[r][c] = '-' if self.board[r][c] == '@' else '.'
            self.board[nr][nc] = '@' if self.board[nr][nc] == '-' else '+'
        elif self.board[nr][nc] in ('$', '*'):
            self.board[r][c] = '-' if self.board[r][c] == '@' else '.'
            self.board[nr][nc] = '@' if self.board[nr][nc] == '$' else '+'
            self.board[nnr][nnc] = '$' if self.board[nnr][nnc] == '-' else '*'

        self.keeper_pos = (nr, nc)

    def process_moves(self, moves):
        for move in moves:
            self.move(move)

    def get_board(self):
        return '\n'.join([''.join(row) for row in self.board])

    
    
    
    
    
    
def main():
    def submit():
        board = text_box.get("1.0", tk.END).strip()
        iterative = iterative_var.get()
        check_bdd = check_bdd_var.get()
        print("Here is your board:")
        print(board)
        print(f"Iterative: {iterative}, Check BDD: {check_bdd}")
        root.destroy()
        run_processes(board, iterative, check_bdd)

    def run_processes(board, iterative, check_bdd):
        # This part runs after the board input is taken
        NumOfBoxes = board.count('*') + board.count('$')
        start = NumOfBoxes
        if iterative == "Yes":
            start = 1
        for i in range(start, NumOfBoxes + 1):
            generator = sokoban_smv_generator(board)
            smv_string = generator.generate_and_get_board(i)  # input: numofboxes to solve
            model_filename = generate_model_file(smv_string, i)
            LURD = generate_result_file(model_filename, i ,check_bdd)  # result filename should be according to iteration
            sokoban_mover = Sokoban_mover(board)
            sokoban_mover.process_moves(LURD)
            board = sokoban_mover.get_board()  # Update the board
            print("   ") 
            print(LURD)
            print("   ")
            print(board)

        print(f"Process completed with Iterative: {iterative} and Check BDD: {check_bdd}")
    
    # Initialize the main window
    root = tk.Tk()
    root.title("Board Input")

    # Create a label
    label = tk.Label(root, text="Enter your board:")
    label.pack()

    # Create a text box for multi-line input
    text_box = tk.Text(root, height=10, width=40)
    text_box.pack()

    # Create a frame for radio buttons
    options_frame = tk.Frame(root)
    options_frame.pack()

    # Create radio buttons for iterative option
    iterative_var = tk.StringVar(value="No")
    tk.Label(options_frame, text="Iterative:").grid(row=0, column=0, sticky=tk.W)
    tk.Radiobutton(options_frame, text="Yes", variable=iterative_var, value="Yes").grid(row=0, column=1)
    tk.Radiobutton(options_frame, text="No", variable=iterative_var, value="No").grid(row=0, column=2)

    # Create radio buttons for check_bdd option
    check_bdd_var = tk.StringVar(value="No")
    tk.Label(options_frame, text="Check BDD:").grid(row=1, column=0, sticky=tk.W)
    tk.Radiobutton(options_frame, text="Yes", variable=check_bdd_var, value="Yes").grid(row=1, column=1)
    tk.Radiobutton(options_frame, text="No", variable=check_bdd_var, value="No").grid(row=1, column=2)

    # Create a submit button
    submit_button = tk.Button(root, text="Submit", command=submit)
    submit_button.pack()

    # Run the GUI loop
    root.mainloop()

if __name__ == "__main__":
    main()



#bunch of boards to choose from (you can also generate using the generator gui for convinience)
# Example usage:
board_str1 = """
#####
#@$.#
#####
"""
# Example usage:
board_str3 = """
#######
#@----#
#--.$-#
#---###
#--$--#
#---#.#
#######
"""
# Example usage:
board_str4 = """
#######
###.###
###$###
#.$@$.#
###$###
###.###
#######
"""
# Example usage:
board_str2 = """
#####
#$@.#
#####
"""
# Example usage:
board_str5 = """
#######
#@----#
#---..#
#--#$$#
#--#--#
#--#--#
#######
"""
# Example usage:
board_str6 = """
########
#@-----#
#----###
#-$-#--#
#---#-$#
#-.-#-.#
########
"""

#    board_str10 = """
##########
###---####
###---#--#
####----.#
####-###.#
##-$-###.#
##-$$#####
##@--#####
##########
#"""

board = """
######
#-.###
#--###
#*@--#
#--$-#
#--###
######
"""
board = """
######
#----#
#--$-#
#.$#.#
#---@#
#---##
######
"""

board2  = """
#######
#-----#
#-----#
#--#--#
#$$$$$#
#..+..#
#######
"""


board2  = """
########
######.#
#--#-..#
#-$$$@.#
#-$---##
#----###
#---####
########
"""
board  = """
######
##---#
##-.-#
#--*-#
#-#-##
#--$-#
##-*-#
##-@-#
######
"""
board  = """
###########
#------####
#--#---.###
#-$-----###
#--@#---###
###----*###
#####-$---#
#######---#
#######.--#
###########
"""
