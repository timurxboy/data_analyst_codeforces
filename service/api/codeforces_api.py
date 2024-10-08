import requests

class CodeforcesAPI:
    BASE_URL = 'https://codeforces.com/api/'

    content_path = 'contest.list'
    user_path = 'user.info'
    user_for_contest = 'contest.standings'
    user_for_rating = 'user.ratedList'
    problem_path = 'problemset.problems'


    def __init__(self, lang='ru'):
        self.lang = lang

    def _make_request(self, method_name, params=None):
        url = f'{self.BASE_URL}{method_name}'
        if not params:
            params = {}
        params['lang'] = self.lang
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'OK':
                    return data['result']
                else:
                    print(f"Error: {data.get('comment', 'Unknown error')}")
            else:
                print(f"HTTP Error: {response.status_code}")
        except Exception as e:
            print(f"Exception occurred: {e}")
        return None

    def get_contest_list(self, gym=False):
        return self._make_request(self.content_path, {'gym': str(gym).lower()})

    def get_user_info(self, handles):
        if isinstance(handles, list):
            handles = ';'.join(handles)
        return self._make_request(self.user_path, {'handles': handles})
    
    def get_users_for_contest(self, contest_id: int):
        return  self._make_request(self.user_for_contest, {'contestId': contest_id})

    def get_users_for_raiting(self):
        return self._make_request(self.user_for_rating, {'activeOnly': False, 'includeRetired': True})

    def get_problemset_problems(self):
        return self._make_request(self.problem_path)

# Пример использования класса

# if __name__ == '__main__':
#     api = CodeforcesAPI()

#     # Пример: получение информации о пользователе
#     user_info = api.get_user_info('tourist')
#     if user_info:
#         api.save_to_json(user_info, 'user_info.json')

#     # Пример: получение задач
#     # problems = api.get_problemset_problems()
#     # if problems:
#     #     api.save_to_json(problems, 'problems.json')

#     # Пример: получение списка контестов
#     contests = api.get_contest_list()
#     if contests:
#         api.save_to_json(contests, 'contests.json')


