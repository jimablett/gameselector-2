import os
import argparse
import chess.pgn
import chess.engine
import sys
import time
import colorama
import subprocess
from collections import defaultdict

colorama.init(autoreset=True)

os.system('cls' if os.name == 'nt' else 'clear')

__script_name__ = '    game-selector 2'
__goal__ = 'Separate good and bad games'
__version__ = '0.2.6_JA'


def print_progress(iteration, total, prefix=''):
    percent = (iteration / total) * 100
    if total > 0:
        percent = min(percent, 100)
    sys.stdout.write(f'\r{colorama.Fore.GREEN}{prefix} : {percent:.0f}% Complete')
    sys.stdout.flush()


def delete_output_files():
    output_folder = 'output'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    for filename in os.listdir(output_folder):
        file_path = os.path.join(output_folder, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")


def open_output_folder():
    output_folder = os.path.abspath('output')
    subprocess.Popen(['explorer.exe', output_folder])


def create_no_bad_games_file():
    output_folder = 'output'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    with open(os.path.join(output_folder, 'no_bad_games_found.txt'), 'w') as f:
        f.write("no bad games were found in this pgn.")


def merge_duplicate_entries(file_path):
    player_stats = defaultdict(int)
    
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                parts = line.split('=')
                if len(parts) == 2:
                    player_name, score = parts
                    player_stats[player_name.strip()] += int(score.strip())
    
    with open(file_path, 'w') as f:
        for player_name, total_score in player_stats.items():
            f.write(f"{player_name} = {total_score}\n")


def main():
    parser = argparse.ArgumentParser(
        prog=__script_name__,
        description=__goal__, epilog='%(prog)s')
    parser.add_argument('--input', required=True, type=str,
                        help='Input pgn filename (required=True).')
    parser.add_argument('--output-good', required=True, type=str,
                        help='Output filename for good games, append mode (required=True).')
    parser.add_argument('--output-bad', required=True, type=str,
                        help='Output filename for bad games, append mode (required=True).')
    parser.add_argument('--engine', required=True, type=str,
                        help='engine filename (required=True).')
    parser.add_argument('--hash', required=False, type=int, default=128,
                        help='engine hash size (required=False, default=128).')
    parser.add_argument('--threads', required=False, type=int, default=1,
                        help='engine threads to use (required=False, default=1).')
    parser.add_argument('--move-time-sec', required=False, type=int, default=1,
                        help='movetime in seconds (required=False, default=1).')
    parser.add_argument('--score-margin', required=False, type=float, default=5.0,
                        help='score margin in pawn unit (required=False, default=5.0).')
    parser.add_argument('-v', '--version', action='version',
                        version=f'{__version__}')                        

    args = parser.parse_args()
    output_goodfn = args.output_good
    output_badfn = args.output_bad
    fn = args.input
    movetimesec = args.move_time_sec
    score_margin = args.score_margin
    enginefn = args.engine
    cnt = 0
    not_removed_games = []

    delete_output_files()

    engine = chess.engine.SimpleEngine.popen_uci(enginefn)
    
    report_data = {
        'wins_on_time': {'White': 0, 'Black': 0},
        'illegal_moves': {'White': 0, 'Black': 0},
        'crashed_games': {'White': 0, 'Black': 0},
        'drawn_in_winning_position': {'White': 0, 'Black': 0},
        'false illegal move claim': {'White': 0, 'Black': 0},
        'false draw claim fifty move rule': {'White': 0, 'Black': 0}    
    }

    with open(fn) as h:
        total_games = sum(1 for line in h if 'White' in line)
        h.seek(0)
        
        while True:
            game = chess.pgn.read_game(h)
                     
            if game is None:
                break
            
            print_progress(cnt, total_games, prefix='Processing games')  
           
            cnt += 1
            
            result = game.headers['Result']
            is_bad = False
            is_save = True
            
            for node in game.mainline():
                parent_node = node.parent
                comment = node.comment                

                if any(keyword in comment for keyword in [
                    'but bare king} 1/2-1/2', 
                    'forfeits on time', 
                    'Arena Adjudication. Illegal move!', 
                    'polyglot: resign (illegal engine move', 
                    'Forfeit due to invalid move', 
                    'wins on time', 
                    'False illegal-move claim',
                    "False draw claim: 'Fifty move rule'",
                    'exited unexpectedly']):
                    is_bad = True

                if is_bad:
                    fen = node.board().fen()
                    print(f' ')
                    print(f'\ngame_num: {cnt}, result: {result}, comment: {comment}')
                    print(f'fen: {fen}')
                    print(f' ')

                    board = chess.Board(fen)
                    info = engine.analyse(board, chess.engine.Limit(time=movetimesec))
                    score_wpov = info['score'].white().score(mate_score=32000)
                    score_wpov /= 100                   

                    if (result == '0-1' and score_wpov > -score_margin) or \
                       (result == '1/2-1/2' and score_wpov > -score_margin) or \
                       (result == '1-0' and score_wpov < score_margin) or \
                       (result == '1/2-1/2' and score_wpov < score_margin):
                        print(f'{colorama.Fore.RED}{colorama.Style.BRIGHT}will not keep this game, eval: {score_wpov} wpov{colorama.Style.RESET_ALL}')
                        print(f'\n ')
                        is_save = False
                      
                    else:
                        print(f'{colorama.Fore.YELLOW}{colorama.Style.BRIGHT}this game will be kept, eval: {score_wpov} wpov{colorama.Style.RESET_ALL}')
                        not_removed_games.append(str(game))
                        print(f' ')
                        is_save = True
                        
                    break
                    
            if is_save:
                with open(output_goodfn, 'a') as f:
                    f.write(f'{game}\n\n')
            else:
                with open(output_badfn, 'a') as f:
                    f.write(f'{game}\n\n')                

    engine.quit()
    
    with open('kept games_(score_margin_reached).pgn', 'w') as f:
        for game in not_removed_games:
            f.write(f'{game}\n\n')


    os.rename('kept games_(score_margin_reached).pgn', os.path.join('output', 'kept games_(score_margin_reached).pgn'))

    print_progress(cnt, total_games, prefix='Processing games')  
    
    if os.path.exists(os.path.join('output', 'bad.pgn')):
        with open(os.path.join('output', 'bad.pgn'), 'r') as bad_pgn_file:
            player_totals = defaultdict(int)
            while True:
                bad_game = chess.pgn.read_game(bad_pgn_file)
                if bad_game is None:
                    break
                    
                white_engine_name = bad_game.headers['White']
                black_engine_name = bad_game.headers['Black']
                result = bad_game.headers['Result']
            
                for node in bad_game.mainline():
                    comment = node.comment                
                    if 'wins on time' in comment:
                        report_data['wins_on_time']['White' if result == '0-1' else 'Black'] += 1
                    elif any(keyword in comment for keyword in [
                        'Arena Adjudication. Illegal move!', 
                        'polyglot: resign (illegal engine move', 
                        'Forfeit due to invalid move']):
                        report_data['illegal_moves']['White' if result == '0-1' else 'Black'] += 1
                    elif 'exited unexpectedly' in comment:
                        report_data['crashed_games']['White' if result == '0-1' else 'Black'] += 1
                    elif 'but bare king} 1/2-1/2' in comment:
                        report_data['drawn_in_winning_position']['White' if result == '1/2-1/2' else 'Black'] += 1
                    elif 'False illegal-move claim' in comment:
                        report_data['false illegal move claim']['White' if result == '0-1' else 'Black'] += 1
                    elif  "False draw claim: 'Fifty move rule'" in comment:
                        report_data['false draw claim fifty move rule']['White' if result == '0-1' else 'Black'] += 1
                
                report_lines = []
                if result == '0-1' or result == '1-0' or result == '1/2-1/2' :
                    report_lines.append(f"White: {white_engine_name}")
                    report_lines.append(f"Black: {black_engine_name}")
                if report_data['wins_on_time']['White'] > 0:
                    report_lines.append(f"game lost on time [White]")
                    report_data['wins_on_time']['White'] = 0
                    player_totals[f"{white_engine_name}_total_bad_games"] += 1
                
                elif report_data['wins_on_time']['Black'] > 0:
                    report_lines.append(f"game lost on time [Black]")
                    report_data['wins_on_time']['Black'] = 0
                    player_totals[f"{black_engine_name}_total_bad_games"] += 1
               
                elif report_data['crashed_games']['White'] > 0:
                    report_lines.append(f"game lost by crash [White]")
                    report_data['crashed_games']['White'] = 0            
                    player_totals[f"{white_engine_name}_total_bad_games"] += 1
                           
                elif report_data['crashed_games']['Black'] > 0:
                    report_lines.append(f"game lost by crash [Black]")
                    report_data['crashed_games']['Black'] = 0            
                    player_totals[f"{black_engine_name}_total_bad_games"] += 1             
                
                elif report_data['illegal_moves']['White'] > 0:
                    report_lines.append(f"game lost by illegal move [White]")                             
                    report_data['illegal_moves']['White'] = 0 
                    player_totals[f"{white_engine_name}_total_bad_games"] += 1
                
                elif report_data['illegal_moves']['Black'] > 0:
                    report_lines.append(f"game lost by illegal move [Black]")
                    report_data['illegal_moves']['Black'] = 0
                    player_totals[f"{black_engine_name}_total_bad_games"] += 1
                        
                elif report_data['drawn_in_winning_position']['White'] > 0:
                    report_lines.append(f"game drawn in winning position [White]")
                    report_data['drawn_in_winning_position']['White'] = 0
                    player_totals[f"{white_engine_name}_total_bad_games"] += 1
                            
                elif report_data['drawn_in_winning_position']['Black'] > 0:
                    report_lines.append(f"game drawn in winning position [Black]")                  
                    report_data['drawn_in_winning_position']['Black'] = 0
                    player_totals[f"{black_engine_name}_total_bad_games"] += 1
                    
                elif report_data['false illegal move claim']['White'] > 0:
                    report_lines.append(f"false illegal move claim [White]")
                    report_data['false illegal move claim']['White'] = 0
                    player_totals[f"{white_engine_name}_total_bad_games"] += 1
                    
                elif report_data['false illegal move claim']['Black'] > 0:
                    report_lines.append(f"false illegal move claim [Black]")
                    report_data['false illegal move claim']['Black'] = 0
                    player_totals[f"{black_engine_name}_total_bad_games"] += 1
                            
                elif report_data['false draw claim fifty move rule']['White'] > 0:
                    report_lines.append(f"false draw claim fifty move rule [White]")                  
                    report_data['false draw claim fifty move rule']['White'] = 0
                    player_totals[f"{black_engine_name}_total_bad_games"] += 1
                    
                elif report_data['false draw claim fifty move rule']['Black'] > 0:
                    report_lines.append(f"false draw claim fifty move rule [Black]")                  
                    report_data['false draw claim fifty move rule']['Black'] = 0
                    player_totals[f"{black_engine_name}_total_bad_games"] += 1
                    
                with open(os.path.join('output', 'players_bad_games.txt'), 'a') as players_file:
                    players_file.write("\n".join(report_lines) + "\n\n")

            with open(os.path.join('output', 'player_totals_bad_games.txt'), 'w') as totals_file:
                for player, total in player_totals.items():
                    totals_file.write(f"\n{player} = {total}\n")

    print_progress(total_games, total_games, prefix='Processing games')  
    
    if cnt == total_games and not os.path.exists(os.path.join('output', 'bad.pgn')):
        create_no_bad_games_file()

    open_output_folder()

    print(f'\n ')


if __name__ == '__main__':
    main()

