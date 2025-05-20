from .player_progress import player_progress

class game_progress():
    def __init__(self,fd):
        self.fd_list = []
        for sock in fd:
            self.fd_list.append(player_progress(sock))
    def incre(self,fd):
        for sock in self.fd_list:
            if sock.socket == fd:
                sock.increment()
            break
    def time(self,fd,time):
         for sock in self.fd_list:
            if sock.socket == fd:
                sock.add_time(time)
            break
    def time_up(self):
        for player in self.fd_list:
            player.finished()
    def announce_results(self, player_list):
    # Step 1: Create a list of tuples (score, player)
        scores = []
        for player in self.fd_list:
            score = player.point_cal()
            scores.append((score, player))

        # Step 2: Sort by score descending
        scores.sort(reverse=True, key=lambda x: x[0])

        # Step 3: Send rank, score, and leaderboard to each player
        leaderboard = "\n[Leaderboard]\n"
        for rank, (score, player) in enumerate(scores, start=1):
            player_obj = player_list.get_player(player.socket)
            player_name = player_obj.name if player_obj else str(player.socket.getpeername())
            leaderboard += f"Rank {rank}: Player {player_name} - Score: {score}\n"

        for rank, (score, player) in enumerate(scores, start=1):
            message = f"\n[Game] Game over! Your score: {score}. Your rank: {rank}.\n{leaderboard}"
            try:
                player.socket.sendall(message.encode())
            except Exception as e:
                print(f"[Log] Failed to send to client: {e}")
