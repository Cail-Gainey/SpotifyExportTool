"""
Spotify API配置信息
"""

# Spotify API凭证
CLIENT_ID = '2a64ff998c0147f7842a4f938feec2f9'
CLIENT_SECRET = 'cb0142ea73564a9db696a61acf59f5a2'
REDIRECT_URI = 'http://127.0.0.1:8080/login/oauth2/code/spotify'
SCOPE = 'user-read-private user-read-email user-read-recently-played user-top-read user-read-playback-state user-modify-playback-state playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private user-follow-read user-follow-modify user-library-read user-library-modify'