#!/usr/bin/env python3
"""
GitHub Repository Analyzer Skill for Hermes Agent
Provides tools to fetch, analyze, and manage GitHub repository data.
Perfect for integrating with your PolarAI project.

Usage in Hermes:
  @github_analyzer get_repo_info
  @github_analyzer get_issues mhaduran-sketch/PolarAI open
  @github_analyzer get_pull_requests mhaduran-sketch/PolarAI
  @github_analyzer get_file_content mhaduran-sketch/PolarAI path/to/file.py
"""

import subprocess
import json
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime


class GitHubAnalyzer:
    """GitHub repository analyzer using GitHub CLI"""

    def __init__(self, repo: str = "mhaduran-sketch/PolarAI"):
        self.repo = repo
        self.gh_available = self._check_gh_cli()

    def _check_gh_cli(self) -> bool:
        """Check if GitHub CLI is available"""
        try:
            subprocess.run(["gh", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  GitHub CLI (gh) not found. Install with: brew install gh (macOS) or apt install gh (Linux)")
            return False

    def _run_gh_command(self, *args) -> Dict[str, Any]:
        """Execute GitHub CLI command and return parsed JSON"""
        try:
            result = subprocess.run(
                ["gh"] + list(args),
                capture_output=True,
                text=True,
                check=True
            )
            return {
                "success": True,
                "data": json.loads(result.stdout) if result.stdout else None,
                "output": result.stdout
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": e.stderr or str(e),
                "data": None
            }
        except json.JSONDecodeError:
            return {
                "success": True,
                "data": None,
                "output": result.stdout
            }

    def get_repo_info(self, repo: Optional[str] = None) -> str:
        """
        Get comprehensive repository information
        
        Returns:
            Repository metadata including description, language, topics, etc.
        """
        repo = repo or self.repo
        result = self._run_gh_command("repo", "view", repo, "--json", 
                                     "name,description,language,topics,isArchived,isPrivate,defaultBranchRef,url,stargazerCount,forkCount,issues")
        
        if result["success"] and result["data"]:
            data = result["data"]
            return f"""
📦 Repository: {data.get('name')}
🔗 URL: {data.get('url')}
📝 Description: {data.get('description', 'No description')}
💻 Language: {data.get('language', 'Not specified')}
🏷️  Topics: {', '.join(data.get('topics', [])) or 'None'}
⭐ Stars: {data.get('stargazerCount', 0)}
🍴 Forks: {data.get('forkCount', 0)}
📋 Open Issues: {data.get('issues', {}).get('totalCount', 0)}
🔐 Private: {data.get('isPrivate', False)}
📌 Default Branch: {data.get('defaultBranchRef', {}).get('name', 'main')}
"""
        else:
            return f"❌ Error fetching repo info: {result.get('error', 'Unknown error')}"

    def get_issues(self, repo: Optional[str] = None, state: str = "open", limit: int = 10) -> str:
        """
        Fetch GitHub issues
        
        Args:
            repo: Repository in format owner/name
            state: Issue state (open, closed, all)
            limit: Number of issues to fetch
            
        Returns:
            Formatted list of issues
        """
        repo = repo or self.repo
        result = self._run_gh_command("issue", "list", "--repo", repo, 
                                     "--state", state, "--limit", str(limit),
                                     "--json", "number,title,body,state,author,createdAt,labels,assignees")
        
        if result["success"] and result["data"]:
            issues = result["data"]
            if not issues:
                return f"✅ No {state} issues found in {repo}"
            
            output = f"\n📋 {state.upper()} ISSUES in {repo} (showing {len(issues)}):\n"
            output += "=" * 70 + "\n"
            
            for issue in issues:
                labels_str = ", ".join([l.get("name", "?") for l in issue.get("labels", [])]) or "none"
                assignees_str = ", ".join([a.get("login", "?") for a in issue.get("assignees", [])]) or "unassigned"
                
                output += f"""
#{issue.get('number')} - {issue.get('title')}
    Author: {issue.get('author', {}).get('login', 'unknown')}
    State: {issue.get('state')}
    Labels: {labels_str}
    Assigned to: {assignees_str}
    Created: {issue.get('createdAt', 'unknown')[:10]}
    Body: {issue.get('body', 'No description')[:200]}...
"""
            return output
        else:
            return f"❌ Error fetching issues: {result.get('error', 'Unknown error')}"

    def get_pull_requests(self, repo: Optional[str] = None, state: str = "open", limit: int = 10) -> str:
        """
        Fetch GitHub pull requests
        
        Args:
            repo: Repository in format owner/name
            state: PR state (open, closed, merged, all)
            limit: Number of PRs to fetch
            
        Returns:
            Formatted list of pull requests
        """
        repo = repo or self.repo
        result = self._run_gh_command("pr", "list", "--repo", repo,
                                     "--state", state, "--limit", str(limit),
                                     "--json", "number,title,body,state,author,createdAt,labels,reviewDecision")
        
        if result["success"] and result["data"]:
            prs = result["data"]
            if not prs:
                return f"✅ No {state} pull requests found in {repo}"
            
            output = f"\n🔀 {state.upper()} PULL REQUESTS in {repo} (showing {len(prs)}):\n"
            output += "=" * 70 + "\n"
            
            for pr in prs:
                labels_str = ", ".join([l.get("name", "?") for l in pr.get("labels", [])]) or "none"
                
                output += f"""
#{pr.get('number')} - {pr.get('title')}
    Author: {pr.get('author', {}).get('login', 'unknown')}
    State: {pr.get('state')}
    Review Decision: {pr.get('reviewDecision', 'pending')}
    Labels: {labels_str}
    Created: {pr.get('createdAt', 'unknown')[:10]}
    Body: {pr.get('body', 'No description')[:200]}...
"""
            return output
        else:
            return f"❌ Error fetching PRs: {result.get('error', 'Unknown error')}"

    def get_file_content(self, repo: Optional[str] = None, path: str = "README.md") -> str:
        """
        Fetch file content from repository
        
        Args:
            repo: Repository in format owner/name
            path: File path in repository
            
        Returns:
            File content or error message
        """
        repo = repo or self.repo
        try:
            result = subprocess.run(
                ["gh", "api", f"repos/{repo}/contents/{path}"],
                capture_output=True,
                text=True,
                check=True
            )
            data = json.loads(result.stdout)
            
            # GitHub API returns base64 encoded content
            import base64
            if "content" in data:
                content = base64.b64decode(data["content"]).decode('utf-8')
                return f"""
📄 File: {path}
Size: {data.get('size', 'unknown')} bytes
URL: {data.get('html_url', 'unknown')}

CONTENT:
{'-' * 70}
{content}
{'-' * 70}
"""
            else:
                return f"❌ Could not find content for {path}"
        except subprocess.CalledProcessError as e:
            return f"❌ Error fetching file: {e.stderr or str(e)}"

    def get_repo_structure(self, repo: Optional[str] = None, path: str = ".") -> str:
        """
        Get repository structure (file tree)
        
        Args:
            repo: Repository in format owner/name
            path: Directory path to list
            
        Returns:
            Repository structure
        """
        repo = repo or self.repo
        result = self._run_gh_command("api", f"repos/{repo}/contents/{path}",
                                     "--jq", "[.[] | {name: .name, type: .type, size: .size}]")
        
        if result["success"] and result["output"]:
            try:
                items = json.loads(result["output"])
                output = f"\n📂 Repository Structure: {repo}/{path}\n"
                output += "=" * 70 + "\n"
                
                for item in items:
                    item_type = "📁" if item.get("type") == "dir" else "📄"
                    size_str = f" ({item.get('size')} bytes)" if item.get("size") else ""
                    output += f"{item_type} {item.get('name')}{size_str}\n"
                
                return output
            except json.JSONDecodeError:
                return f"❌ Error parsing repository structure"
        else:
            return f"❌ Error fetching structure: {result.get('error', 'Unknown error')}"

    def get_latest_commits(self, repo: Optional[str] = None, limit: int = 10) -> str:
        """
        Get latest commits from repository
        
        Args:
            repo: Repository in format owner/name
            limit: Number of commits to fetch
            
        Returns:
            Formatted list of commits
        """
        repo = repo or self.repo
        result = self._run_gh_command("api", f"repos/{repo}/commits",
                                     "--jq", f".[0:{limit}] | [.[] | {{sha: .sha[0:7], message: .commit.message, author: .commit.author.name, date: .commit.author.date}}]")
        
        if result["success"] and result["output"]:
            try:
                commits = json.loads(result["output"])
                output = f"\n📝 Latest Commits in {repo} (showing {len(commits)}):\n"
                output += "=" * 70 + "\n"
                
                for commit in commits:
                    output += f"""
{commit.get('sha')} - {commit.get('message').split(chr(10))[0][:60]}
    Author: {commit.get('author', 'unknown')}
    Date: {commit.get('date', 'unknown')[:10]}
"""
                return output
            except json.JSONDecodeError:
                return f"❌ Error parsing commits"
        else:
            return f"❌ Error fetching commits: {result.get('error', 'Unknown error')}"

    def create_issue(self, repo: Optional[str] = None, title: str = "", body: str = "", labels: List[str] = None) -> str:
        """
        Create a new GitHub issue
        
        Args:
            repo: Repository in format owner/name
            title: Issue title
            body: Issue description
            labels: List of labels
            
        Returns:
            Issue creation confirmation
        """
        repo = repo or self.repo
        
        if not title:
            return "❌ Issue title is required"
        
        cmd = ["issue", "create", "--repo", repo, "--title", title]
        if body:
            cmd.extend(["--body", body])
        if labels:
            cmd.extend(["--label", ",".join(labels)])
        
        result = self._run_gh_command(*cmd)
        
        if result["success"]:
            return f"✅ Issue created successfully!\n{result.get('output', '')}"
        else:
            return f"❌ Error creating issue: {result.get('error', 'Unknown error')}"


def main():
    """Main entry point for skill"""
    analyzer = GitHubAnalyzer()
    
    if not analyzer.gh_available:
        print("GitHub CLI is required. Install it first.")
        return
    
    # Example usage
    print(analyzer.get_repo_info())
    print("\n" + analyzer.get_issues(limit=5))
    print("\n" + analyzer.get_pull_requests(limit=5))
    print("\n" + analyzer.get_latest_commits(limit=5))


if __name__ == "__main__":
    main()
