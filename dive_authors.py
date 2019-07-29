import click
import csv
import datetime
import os
import requests
import shutil
import subprocess

from gitinspector import filtering
from gitinspector.changes import Commit, FileDiff, AuthorInfo
from tempfile import mkdtemp

COLUMN_HEADERS = [
    'Author',
    'Date',
    'Repository',
    'Lines added',
    'Lines deleted',
]


class DiveRunner(object):
    def __init__(self, outwriter, year):

        self.outwriter = outwriter

        self.project_name = ''

        self.hard = False

        self.include_metrics = False
        self.list_file_types = True
        self.localize_output = False
        self.repo = '.'
        self.responsibilities = False
        self.grading = False
        self.timeline = False
        self.useweeks = False
        self.year = year

    def output(self):
        previous_directory = os.getcwd()

        os.chdir(self.repo)

        the_changes = Changes(self.hard)

        authordateinfo_list = the_changes.get_authordateinfo_list()

        for date_string, author_name in sorted(authordateinfo_list):
            authorinfo = authordateinfo_list.get(
                (date_string, author_name),
            )

            change = datetime.datetime.strptime(date_string, '%Y-%m-%d')

            if change > datetime.datetime(self.year, 1, 1) and change < datetime.datetime(self.year + 1, 1, 1):
                self.outwriter.writerow([
                    author_name,
                    date_string,
                    self.project_name,
                    authorinfo.insertions,
                    authorinfo.deletions,
                ])

        os.chdir(previous_directory)


class Changes(object):
    def __init__(self, hard=False):
        self.commits = []

        self.authors = {}
        self.authors_dateinfo = {}
        self.authors_by_email = {}
        self.emails_by_author = {}

        git_log_r = subprocess.Popen(
            'git log --reverse --pretty="%cd|%H|%aN|%aE" --stat=100000,8192 --no-merges -w ' +
            '{0} --date=short'.format('-C -C -M' if hard else ''),
            shell=True, bufsize=1, stdout=subprocess.PIPE).stdout
        commit = None
        lines = git_log_r.readlines()

        for i in lines:
            j = i.strip().decode('unicode_escape', 'ignore')
            j = j.encode('latin-1', 'replace')
            j = j.decode('utf-8', 'replace')

            if Commit.is_commit_line(j):
                (author, email) = Commit.get_author_and_email(j)
                self.emails_by_author[author] = email
                self.authors_by_email[email] = author

            if Commit.is_commit_line(j) or i is lines[-1]:
                if commit is not None:
                    self.commits.append(commit)
                commit = Commit(j)

            if FileDiff.is_filediff_line(j) and not filtering.set_filtered(
                    FileDiff.get_filename(j)) and not \
                    filtering.set_filtered(commit.author,
                                           'author') and not filtering.set_filtered(
                commit.email, 'email') and not \
                    filtering.set_filtered(commit.sha, 'revision'):

                filediff = FileDiff(j)
                commit.add_filediff(filediff)

        if len(self.commits) > 0:
            self.first_commit_date = datetime.date(
                int(self.commits[0].date[0:4]), int(self.commits[0].date[5:7]),
                int(self.commits[0].date[8:10]))
            self.last_commit_date = datetime.date(
                int(self.commits[-1].date[0:4]),
                int(self.commits[-1].date[5:7]),
                int(self.commits[-1].date[8:10]))

    def get_commits(self):
        return self.commits

    def __modify_authorinfo__(self, authors, key, commit):
        if authors.get(key, None) is None:
            authors[key] = AuthorInfo()

        if commit.get_filediffs():
            authors[key].commits += 1

        for j in commit.get_filediffs():
            authors[key].insertions += j.insertions
            authors[key].deletions += j.deletions

    def get_authorinfo_list(self):
        if not self.authors:
            for i in self.commits:
                self.__modify_authorinfo__(self.authors, i.author, i)

        return self.authors

    def get_authordateinfo_list(self):
        if not self.authors_dateinfo:
            for i in self.commits:
                self.__modify_authorinfo__(self.authors_dateinfo,
                                           (i.date, i.author), i)

        return self.authors_dateinfo


def get_all_repos(access_token):
    repos = []
    page = 1
    url = 'https://api.github.com/orgs/industrydive/repos?per_page=100&page=%s&access_token=%s'
    while True:
        response = requests.get(url % (page, access_token))

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print 'Error: %s' % e

        response_json = response.json()
        for repo in response_json:
            repos.append({
                'name': repo['name'],
                'ssh_url': repo['ssh_url'],
            })
        if len(response_json) == 100:
            page = page + 1
        else:
            break

    return repos


@click.command()
@click.option(
    '--year',
    default=datetime.datetime.today().year - 1,
    help='Year to run git-authors for. Defaults to the previous year',
)
@click.option(
    '--access-token',
    help='Create a Github access token',
)
@click.option(
    '--outfile',
    'outfile_name',
    default='git_stats.csv',
    help='File name to write the git stats to',
    required=True,
)
def main(year, access_token, outfile_name):
    script_path = os.path.dirname(os.path.abspath(__file__))
    path_to_outfile = os.path.join(script_path, outfile_name)

    # create a temporary directory
    temp_dir_path = mkdtemp()
    os.chdir(temp_dir_path)

    try:
        with open(path_to_outfile, 'wb') as outfile:
            outwriter = csv.writer(outfile)
            outwriter.writerow(COLUMN_HEADERS)

            repos = get_all_repos(access_token)

            for repo in repos:
                os.system('git clone %s' % repo['ssh_url'])
                repo_path = os.path.join(temp_dir_path, repo['name'])

                runner = DiveRunner(outwriter, year)
                runner.repo = repo_path
                runner.project_name = repo['name']

                runner.output()
    finally:
        # clean up our temp directory
        shutil.rmtree(temp_dir_path)


if __name__ == '__main__':
    main()
