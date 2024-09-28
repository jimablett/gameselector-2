import os
import argparse
import chess.pgn
import chess.engine
import sys
import time
import colorama

colorama.init(autoreset=True)

os.system('cls' if os.name == 'nt' else 'clear')

__script_name__ = 'game-selector 2'
__goal__ = 'Separate good and bad games'
__version__ = '0.2.2_JA'


def print_progress(iteration, total, prefix=''):
    percent = (iteration / total) * 100 * 44  
    if percent > 100: 
        percent = 100
    sys.stdout.write(f'\r{colorama.Fore.GREEN}{prefix} : {percent:.0f}% Complete')
    sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(
        prog='%s' % __script_name__,
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

    engine = chess.engine.SimpleEngine.popen_uci(enginefn)

    with open(fn) as h:
        total_games = sum(1 for _ in h)
        h.seek(0)

        while True:
            game = chess.pgn.read_game(h)
            if game is None:
                break
            cnt += 1
            print_progress(cnt, total_games, prefix='Processing games')

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
                    'exited unexpectedly']):
                    is_bad = True

                if is_bad:
                    fen = node.board().fen()  # pos after move
                    print(f' ')
                    print(f'\ngame_num: {cnt}, result: {result}, comment: {comment}')
                    print(f'fen: {fen}')
                    print(f' ')

                    board = chess.Board(fen)
                    info = engine.analyse(board, chess.engine.Limit(time=movetimesec))
                    score_wpov = info['score'].white().score(mate_score=32000)
                    score_wpov/=100

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
    
    with open('kept games_(score_margin_reached).txt', 'w') as f:
        for game in not_removed_games:
            f.write(f'{game}\n\n')
            
    print(f'{colorama.Fore.GREEN}\n\nProcessing games : 100% Complete')
   
   
    print('\nProcessing complete.')

if __name__ == '__main__':
    main()

