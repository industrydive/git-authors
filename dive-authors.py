# from gitinspector import extensions
from gitinspector import filtering
from gitinspector.changes import Commit, FileDiff, AuthorInfo
import os
import subprocess
import datetime


project_names = ('sailthru_tools', 'containers', 'sailthru-python-client', 'dive_sailthru_client', 'dive-email-inliner', 'sassy-ink')
projects_path = os.path.join('/', 'Users', 'david', 'Development', 'work')


class DiveRunner(object):
    def __init__(self):
        self.project_name = ''

        self.hard = False

        self.include_metrics = False
        self.list_file_types = True
        self.localize_output = False
        self.repo = "."
        self.responsibilities = False
        self.grading = False
        self.timeline = False
        self.useweeks = False

    def output(self):
        previous_directory = os.getcwd()

        os.chdir(self.repo)

        the_changes = Changes(self.hard)

        authordateinfo_list = the_changes.get_authordateinfo_list()

        row = '"{author}","{date}","{project}","{added}","{deleted}"'

        for date_string, author_name in sorted(authordateinfo_list):
            authorinfo = authordateinfo_list.get(
                (date_string, author_name)
            )

            print row.format(
                author=author_name,
                date=date_string,
                project=self.project_name,
                added=authorinfo.insertions,
                deleted=authorinfo.deletions
            )

        os.chdir(previous_directory)


class Changes(object):
    def __init__(self, hard=False):
        self.commits = []

        self.authors = {}
        self.authors_dateinfo = {}
        self.authors_by_email = {}
        self.emails_by_author = {}

        git_log_r = subprocess.Popen(
            "git log --reverse --pretty=\"%cd|%H|%aN|%aE\" --stat=100000,8192 --no-merges -w " +
            "{0} --date=short".format("-C -C -M" if hard else ""),
            shell=True, bufsize=1, stdout=subprocess.PIPE).stdout
        commit = None
        found_valid_extension = False
        lines = git_log_r.readlines()

        for i in lines:
            j = i.strip().decode("unicode_escape", "ignore")
            j = j.encode("latin-1", "replace")
            j = j.decode("utf-8", "replace")

            if Commit.is_commit_line(j):
                (author, email) = Commit.get_author_and_email(j)
                self.emails_by_author[author] = email
                self.authors_by_email[email] = author

            if Commit.is_commit_line(j) or i is lines[-1]:
                if found_valid_extension:
                    self.commits.append(commit)

                found_valid_extension = False
                commit = Commit(j)

            if FileDiff.is_filediff_line(j) and not filtering.set_filtered(
                    FileDiff.get_filename(j)) and not \
                    filtering.set_filtered(commit.author,
                                           "author") and not filtering.set_filtered(
                commit.email, "email") and not \
                    filtering.set_filtered(commit.sha, "revision"):
                # extensions.add_located(FileDiff.get_extension(j))

                if is_valid_extension(j):
                    found_valid_extension = True
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
        if authors.get(key, None) == None:
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

    def get_latest_author_by_email(self, name):
        if not hasattr(name, 'decode'):
            name = str.encode(name)

        name = name.decode("unicode_escape", "ignore")
        return self.authors_by_email[name]

    def get_latest_email_by_author(self, name):
        return self.emails_by_author[name]

def is_valid_extension(string):
    """
    Hacky way to say all extensions are valid.
    :param str string: The commit line.
    :return: True
    """
    return True

def main():
    for project_name in project_names:
        repo_path = os.path.join(projects_path, project_name)

        runner = DiveRunner()
        runner.repo = repo_path
        runner.project_name = project_name

        runner.output()


if __name__ == "__main__":
    main()
