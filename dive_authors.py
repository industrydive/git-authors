# from gitinspector import extensions
from gitinspector import filtering
from gitinspector.changes import Commit, FileDiff, AuthorInfo
import os
import subprocess
import datetime
import csv

# A list of repositories updated after 01/01/2018
PROJECT_NAMES = (
    'django-autosave',
    'datadump',
    'mr-clean',
    'dive-dr',
    'TarPy',
    'django-dbsettings',
    'django-site-metatags',
    'CIOregontrail',
    'django-ckeditor',
    'divesite-docker',
    'es6-presentation',
    'fileflow',
    'dive-brand-studio',
    'Secret-Santakkuh',
    'easy_django_mockups',
    'living-styleguide',
    'link-tracker',
    'sourcelist',
    'incident-response-docs',
    'locustdive',
    'dive-design-system',
    'js-tools',
    'dragonclaw',
    'dive_sailthru_updater',
    'lytics-tools',
    'dive-kickstart',
    'leadsquared-tools',
    'scrapinghub-event-sites',
    'dive-form-fields',
    'support',
    'lambdas',
    'designsite',
    'sourcedive',
    'dive_audience_tools',
    'dive-ad-templates',
    'styleguidefail',
    'corporate-site',
    'cloudflare-tools',
    'dive_sailthru_client',
    'sailthru_tools',
    'accountant',
    'datadive',
    'rlpsys',
    'datascripts',
    'dive-email-inliner',
    'divesite',
)
PROJECTS_PATH = './'  # os.path.join('/', 'Users', 'david', 'Development', 'work')
OUTFILENAME = 'git_stats.csv'

COLUMN_HEADERS = (
    'Author',
    'Date',
    'Repository',
    'Lines added',
    'Lines deleted',
)


class DiveRunner(object):
    def __init__(self, outwriter):

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

    def output(self):
        previous_directory = os.getcwd()

        os.chdir(self.repo)

        the_changes = Changes(self.hard)

        authordateinfo_list = the_changes.get_authordateinfo_list()

        # row = '"{author}","{date}","{project}","{added}","{deleted}"'

        for date_string, author_name in sorted(authordateinfo_list):
            authorinfo = authordateinfo_list.get(
                (date_string, author_name),
            )

            change = datetime.datetime.strptime(date_string, '%Y-%m-%d')

            if change > datetime.datetime(2018, 1, 1) and change < datetime.datetime(2019, 1, 1):
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


def main():
    with open(OUTFILENAME, 'wb') as outfile:
        outwriter = csv.writer(outfile)

        outwriter.writerow(*COLUMN_HEADERS)

        for project_name in PROJECT_NAMES:
            os.system('git clone git@github.com:industrydive/%s' % project_name)
            repo_path = os.path.join(PROJECTS_PATH, project_name)

            runner = DiveRunner(outwriter)
            runner.repo = repo_path
            runner.project_name = project_name

            runner.output()


if __name__ == '__main__':
    main()
