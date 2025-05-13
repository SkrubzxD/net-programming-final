def send_menu(fd, player_list):
    main_menu = """\n
---------------------
|        HOME       |
| 1. create room    |
| 2. join room      |
| 3. list room      |
| x. leave game     |
---------------------
"""
    game_menu_guest = """\n
---------------------
|       ROOM        |
| 1. start          |
| 2. chat           |
| x. leave room     |    
---------------------
"""
    game_menu_host = """\n
---------------------
|    ROOM (HOST)    |  
| 1. start          |
| 2. chat           |
| x. disban         |
---------------------
"""
    player = player_list.get_player(fd)
    if not player.in_room:
        return main_menu
    else:
        if not player.in_game and player_list.check_host(fd) == -1:
            return game_menu_guest
        elif not player.in_game and player_list.check_host(fd) != -1:
            return game_menu_host