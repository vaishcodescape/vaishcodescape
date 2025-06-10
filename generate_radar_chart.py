import requests
import matplotlib.pyplot as plt
import numpy as np
import logging
import sys
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

GITHUB_USER = 'vaishcodescape'
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')  # Get token from environment variable

# Fetch all public repos
def get_repos(user):
    try:
        repos = []
        page = 1
        headers = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}
        while True:
            url = f'https://api.github.com/users/{user}/repos?per_page=100&page={page}'
            r = requests.get(url, headers=headers)
            r.raise_for_status()  # Raise an exception for bad status codes
            data = r.json()
            if not data:
                break
            repos.extend([repo['name'] for repo in data])
            page += 1
        logging.info(f"Successfully fetched {len(repos)} repositories")
        return repos
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching repositories: {e}")
        raise

# Fetch activity stats
def get_activity(user, repos):
    try:
        stats = {
            'Commits': 0,
            'Pull requests': 0,
            'Issues': 0,
            'Code review': 0
        }
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {GITHUB_TOKEN}'
        } if GITHUB_TOKEN else {'Accept': 'application/vnd.github.v3+json'}
        
        for repo in repos:
            logging.info(f"Processing repository: {repo}")
            # Commits
            commits_url = f'https://api.github.com/repos/{user}/{repo}/commits?author={user}'
            commits = requests.get(commits_url, headers=headers)
            commits.raise_for_status()
            commits_data = commits.json()
            stats['Commits'] += len(commits_data) if isinstance(commits_data, list) else 0
            
            # PRs
            prs_url = f'https://api.github.com/repos/{user}/{repo}/pulls?state=all&per_page=100'
            prs = requests.get(prs_url, headers=headers)
            prs.raise_for_status()
            prs_data = prs.json()
            stats['Pull requests'] += len([pr for pr in prs_data if pr.get('user', {}).get('login') == user]) if isinstance(prs_data, list) else 0
            
            # Issues
            issues_url = f'https://api.github.com/repos/{user}/{repo}/issues?state=all&per_page=100'
            issues = requests.get(issues_url, headers=headers)
            issues.raise_for_status()
            issues_data = issues.json()
            stats['Issues'] += len([issue for issue in issues_data if issue.get('user', {}).get('login') == user and 'pull_request' not in issue]) if isinstance(issues_data, list) else 0
            
            # Code reviews
            reviews_url = f'https://api.github.com/repos/{user}/{repo}/pulls?state=all&per_page=100'
            prs_for_reviews = requests.get(reviews_url, headers=headers)
            prs_for_reviews.raise_for_status()
            prs_for_reviews_data = prs_for_reviews.json()
            
            for pr in prs_for_reviews_data if isinstance(prs_for_reviews_data, list) else []:
                pr_number = pr.get('number')
                reviews_api = f'https://api.github.com/repos/{user}/{repo}/pulls/{pr_number}/reviews'
                reviews = requests.get(reviews_api, headers=headers)
                reviews.raise_for_status()
                reviews_data = reviews.json()
                stats['Code review'] += len([review for review in reviews_data if review.get('user', {}).get('login') == user]) if isinstance(reviews_data, list) else 0
        
        logging.info(f"Activity stats collected: {stats}")
        return stats
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching activity stats: {e}")
        raise

def plot_radar(stats):
    try:
        labels = list(stats.keys())
        values = list(stats.values())
        total = sum(values)
        if total == 0:
            values = [1 for _ in values]  # Avoid division by zero
            total = len(values)
        percentages = [v / total * 100 for v in values]
        labels = [f'{int(p)}%\n{l}' for p, l in zip(percentages, labels)]
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        values += values[:1]
        angles += angles[:1]
        
        plt.figure(figsize=(6, 6), facecolor='#181c23')
        ax = plt.subplot(111, polar=True, facecolor='#181c23')
        ax.plot(angles, values, 'o-', linewidth=2, color='#39ff14')
        ax.fill(angles, values, alpha=0.25, color='#39ff14')
        ax.set_thetagrids(np.degrees(angles[:-1]), labels, color='#b0b7c3')
        ax.set_yticklabels([])
        ax.spines['polar'].set_color('#39ff14')
        plt.tight_layout()
        plt.savefig('activity.png', bbox_inches='tight', facecolor='#181c23')
        plt.close()
        logging.info("Radar chart generated successfully")
    except Exception as e:
        logging.error(f"Error generating radar chart: {e}")
        raise

def main():
    try:
        logging.info("Starting radar chart generation")
        repos = get_repos(GITHUB_USER)
        stats = get_activity(GITHUB_USER, repos)
        plot_radar(stats)
        logging.info("Radar chart generation completed successfully")
    except Exception as e:
        logging.error(f"Failed to generate radar chart: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 