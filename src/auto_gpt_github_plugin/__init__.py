"""This is the Github plugin for Auto-GPT."""
import os
from typing import Any, Dict, List, Optional, Tuple, TypeVar, TypedDict
from auto_gpt_plugin_template import AutoGPTPluginTemplate
from github import Github, Consts
from github.Repository import Repository

# import autogpt
# autogpt.commands.web_selenium.browse_website("https://github.com/Significant-Gravitas/Auto-GPT/issues/2689", question)

# import autogpt
# autogpt.processing.text.summary.summarize_text(url, text, question, None)

PromptGenerator = TypeVar("PromptGenerator")


class Message(TypedDict):
    role: str
    content: str


class Commands:
    YOUR_USERNAME = "your_username_on_github"
    CREATE_REPO = "create_repo_on_github"
    YOUR_REPOS = "your_repositories_on_github"
    OPEN_REPO = "change_github_repository"
    GET_NEXT_OPEN_ISSUE = "read_next_open_github_issue"
    REPLY_TO_ISSUE = "reply_to_last_github_issue"


NO_REPO_ERROR_MSG = f"You have not selected a Github Repo. You can view your repositories with the command '{Commands.YOUR_REPOS}' and select a repository with the command '{Commands.OPEN_REPO}'."


class AutoGPTGithubPlugin(AutoGPTPluginTemplate):
    """
    This is the Auto-GPT Github plugin.
    """

    def __init__(self):
        super().__init__()
        self._name = "Auto-GPT-Github-Plugin"
        self._version = "0.1.0"
        self._description = "Auto-GPT Github Plugin: Supercharge Github management."
        token = os.getenv("GITHUB_ACCESS_TOKEN")
        githubURL = os.getenv("GITHUB_BASE_URL")
        if not githubURL:
            githubURL = Consts.DEFAULT_BASE_URL

        self.g = Github(base_url=githubURL, login_or_token=token)
        self.user = self.g.get_user
        defaultRepo = os.getenv("GITHUB_DEFAULT_REPO")
        if defaultRepo:
            self.currentRepo: Repository = self.g.get_repo(defaultRepo)
        self.readIssueNumbers = []

    def readNextOpenIssue(self):
        if not self.currentRepo:
            return NO_REPO_ERROR_MSG
        open_issues = self.currentRepo.get_issues(state="open")
        for issue in open_issues:
            if issue.number in self.readIssueNumbers:
                continue
            for reaction in issue.get_reactions():
                if reaction.content == "+1" and reaction.user == self.user:
                    continue
            self.readIssueNumbers.append(issue.number)
            return f"The issue has the title and text '{issue.title}':'{issue.body}'.\n\nTo reply to this issue, use your command: '{Commands.REPLY_TO_ISSUE}'"

    def replyToLastIssue(self, text):
        if not self.currentRepo:
            return NO_REPO_ERROR_MSG
        if not self.readIssueNumbers:
            return f"You have not read any Issues. Use the command '{Commands.GET_NEXT_OPEN_ISSUE}' to read your first Github issue."
        issue = self.currentRepo.get_issue(self.readIssueNumbers[-1])
        issue.create_comment(text)
        issue.create_reaction("+1")
        return f"The comment was successfully added!"

    def getRepositoriesOfCurrentUser(self):
        repos = self.g.get_user().get_repos()
        if not repos:
            return f"Your user {self.g.get_user()} has no Github repositories."
        result = "The user has the following repositories:\n"
        for repo in repos:
            result += f"- The repository with the name '{repo.name}' with {repo.stargazers_count} Github Stars last modified on '{repo.last_modified}';\n"
        return result

    def openRepo(self, name):
        repo = self.g.get_user().get_repo(name)
        if not repo:
            return f"Github Repository {name} was not found."
        self.currentRepo = repo
        return f"You have navigated to the Github Repository '{name}'"

    def post_prompt(self, prompt: PromptGenerator) -> PromptGenerator:
        g = self.g
        user = g.get_user()
        """
        prompt.add_command(
            "Github: Get your username", Commands.YOUR_USERNAME, {}, g.get_user
        )

        prompt.add_command(
            "create a new Github repository",
            Commands.CREATE_REPO,
            {
                "name": "<Github Repository Name>",
            },
            user.create_repo,
        )

        prompt.add_command(
            "get the names of all your Github repositories",
            Commands.YOUR_REPOS,
            {},
            self.getRepositoriesOfCurrentUser,
        )
        """
        prompt.add_command(
            "read the next open issue in your current Github repository",
            Commands.GET_NEXT_OPEN_ISSUE,
            {},
            self.readNextOpenIssue,
        )

        prompt.add_command(
            f"reply to the last GitHub issue read with '{Commands.GET_NEXT_OPEN_ISSUE}'",
            Commands.REPLY_TO_ISSUE,
            {
                "text": "<text that is used to reply>",
            },
            self.replyToLastIssue,
        )

        prompt.add_command(
            "Open or Change your Github Repository",
            Commands.OPEN_REPO,
            {"name": "<Github Repository Name>"},
            self.openRepo,
        )

        return prompt

    def can_handle_post_prompt(self) -> bool:
        """This method is called to check that the plugin can
        handle the post_prompt method.

        Returns:
            bool: True if the plugin can handle the post_prompt method."""
        return True

    def can_handle_on_response(self) -> bool:
        """This method is called to check that the plugin can
        handle the on_response method.

        Returns:
            bool: True if the plugin can handle the on_response method."""
        return False

    def on_response(self, response: str, *args, **kwargs) -> str:
        """This method is called when a response is received from the model."""
        pass

    def can_handle_on_planning(self) -> bool:
        """This method is called to check that the plugin can
        handle the on_planning method.

        Returns:
            bool: True if the plugin can handle the on_planning method."""
        return False

    def on_planning(
        self, prompt: PromptGenerator, messages: List[Message]
    ) -> Optional[str]:
        """This method is called before the planning chat completion is done.

        Args:
            prompt (PromptGenerator): The prompt generator.
            messages (List[str]): The list of messages.
        """
        pass

    def can_handle_post_planning(self) -> bool:
        """This method is called to check that the plugin can
        handle the post_planning method.

        Returns:
            bool: True if the plugin can handle the post_planning method."""
        return False

    def post_planning(self, response: str) -> str:
        """This method is called after the planning chat completion is done.

        Args:
            response (str): The response.

        Returns:
            str: The resulting response.
        """
        pass

    def can_handle_pre_instruction(self) -> bool:
        """This method is called to check that the plugin can
        handle the pre_instruction method.

        Returns:
            bool: True if the plugin can handle the pre_instruction method."""
        return False

    def pre_instruction(self, messages: List[Message]) -> List[Message]:
        """This method is called before the instruction chat is done.

        Args:
            messages (List[Message]): The list of context messages.

        Returns:
            List[Message]: The resulting list of messages.
        """
        pass

    def can_handle_on_instruction(self) -> bool:
        """This method is called to check that the plugin can
        handle the on_instruction method.

        Returns:
            bool: True if the plugin can handle the on_instruction method."""
        return False

    def on_instruction(self, messages: List[Message]) -> Optional[str]:
        """This method is called when the instruction chat is done.

        Args:
            messages (List[Message]): The list of context messages.

        Returns:
            Optional[str]: The resulting message.
        """
        pass

    def can_handle_post_instruction(self) -> bool:
        """This method is called to check that the plugin can
        handle the post_instruction method.

        Returns:
            bool: True if the plugin can handle the post_instruction method."""
        return False

    def post_instruction(self, response: str) -> str:
        """This method is called after the instruction chat is done.

        Args:
            response (str): The response.

        Returns:
            str: The resulting response.
        """
        pass

    def can_handle_pre_command(self) -> bool:
        """This method is called to check that the plugin can
        handle the pre_command method.

        Returns:
            bool: True if the plugin can handle the pre_command method."""
        return False

    def pre_command(
        self, command_name: str, arguments: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """This method is called before the command is executed.

        Args:
            command_name (str): The command name.
            arguments (Dict[str, Any]): The arguments.

        Returns:
            Tuple[str, Dict[str, Any]]: The command name and the arguments.
        """
        pass

    def can_handle_post_command(self) -> bool:
        """This method is called to check that the plugin can
        handle the post_command method.

        Returns:
            bool: True if the plugin can handle the post_command method."""
        return False

    def post_command(self, command_name: str, response: str) -> str:
        """This method is called after the command is executed.

        Args:
            command_name (str): The command name.
            response (str): The response.

        Returns:
            str: The resulting response.
        """
        pass

    def can_handle_chat_completion(
        self, messages: Dict[Any, Any], model: str, temperature: float, max_tokens: int
    ) -> bool:
        """This method is called to check that the plugin can
          handle the chat_completion method.

        Args:
            messages (List[Message]): The messages.
            model (str): The model name.
            temperature (float): The temperature.
            max_tokens (int): The max tokens.

          Returns:
              bool: True if the plugin can handle the chat_completion method."""
        return False

    def handle_chat_completion(
        self, messages: List[Message], model: str, temperature: float, max_tokens: int
    ) -> str:
        """This method is called when the chat completion is done.

        Args:
            messages (List[Message]): The messages.
            model (str): The model name.
            temperature (float): The temperature.
            max_tokens (int): The max tokens.

        Returns:
            str: The resulting response.
        """
        pass
