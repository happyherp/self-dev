# GitHub Token Setup for SIP (Self-Improving Program)

This document provides step-by-step instructions for creating a GitHub Personal Access Token (PAT) with the minimal permissions required for the SIP project.

## 🎯 **Why You Need This Token**

SIP requires a GitHub token to:
- Read repository contents and structure
- Fetch issue details and metadata
- Create branches for proposed solutions
- Commit code changes to branches
- Create pull requests with solutions
- Read repository files for context analysis

## 🔐 **Security Principle: Minimal Permissions**

This guide follows the **principle of least privilege** - the token will have only the minimum permissions needed for SIP to function, reducing security risk.

## 📋 **Step-by-Step Token Creation**

### 1. Navigate to GitHub Token Settings
1. Go to [GitHub.com](https://github.com) and sign in
2. Click your profile picture (top-right corner)
3. Select **Settings** from the dropdown
4. In the left sidebar, scroll down and click **Developer settings**
5. Click **Personal access tokens**
6. Click **Tokens (classic)** *(recommended for SIP)*

### 2. Generate New Token
1. Click **Generate new token**
2. Select **Generate new token (classic)**
3. You may be prompted to confirm your password

### 3. Configure Token Settings

#### **Token Name (Note)**
```
SIP - Self-Improving Program
```

#### **Expiration**
- **Recommended**: 90 days (for security)
- **Alternative**: No expiration (if you prefer convenience)

#### **Required Scopes (Permissions)**

Select **ONLY** these scopes - do not select additional permissions:

##### ✅ **repo** (Full control of private repositories)
- ✅ `repo:status` - Access commit status
- ✅ `repo_deployment` - Access deployment status  
- ✅ `public_repo` - Access public repositories
- ✅ `repo:invite` - Access repository invitations
- ✅ `security_events` - Read and write security events

*Note: The `repo` scope includes all sub-scopes above. You only need to check the main `repo` checkbox.*

##### ✅ **workflow** (Update GitHub Action workflows)
- This allows SIP to work with repositories that have GitHub Actions

#### **Scopes NOT Needed (Do NOT select)**
- ❌ `admin:repo_hook` - SIP doesn't manage webhooks
- ❌ `admin:org` - SIP doesn't need organization admin rights
- ❌ `admin:public_key` - SIP doesn't manage SSH keys
- ❌ `admin:org_hook` - SIP doesn't manage organization webhooks
- ❌ `gist` - SIP doesn't create gists
- ❌ `notifications` - SIP doesn't manage notifications
- ❌ `user` - SIP doesn't need user profile access
- ❌ `delete_repo` - SIP should never delete repositories
- ❌ `admin:gpg_key` - SIP doesn't manage GPG keys

### 4. Generate and Save Token
1. Click **Generate token** at the bottom
2. **IMPORTANT**: Copy the token immediately - you won't see it again!
3. Store it securely (see storage recommendations below)

## 🔒 **Secure Token Storage**

### **For Development/Testing**
Create a `.env` file in your project root:
```bash
# .env (add to .gitignore!)
GITHUB_TOKEN=ghp_your_token_here_1234567890abcdef
```

### **For Production/CI**
Add as repository secrets:
1. Go to your repository on GitHub
2. Click **Settings** tab
3. Click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Name: `GITHUB_TOKEN`
6. Value: Your token
7. Click **Add secret**

### **For Local Development**
Add to your shell profile (`.bashrc`, `.zshrc`, etc.):
```bash
export GITHUB_TOKEN="ghp_your_token_here_1234567890abcdef"
```

## ✅ **Verify Token Works**

Test your token with SIP:

```bash
# Set the token
export GITHUB_TOKEN="your_token_here"

# Test SIP can access GitHub
uv run python -m sip process-issue happyherp/self-dev 1 --dry-run
```

You should see SIP successfully fetch the issue without errors.

## 🔄 **Token Rotation (Security Best Practice)**

### **When to Rotate**
- Every 90 days (if you set expiration)
- If token is accidentally exposed
- When team members leave
- After security incidents

### **How to Rotate**
1. Create new token following this guide
2. Update all places where old token is stored
3. Test new token works
4. Delete old token from GitHub

## 🚨 **Security Warnings**

### **Never Do This**
- ❌ Commit tokens to git repositories
- ❌ Share tokens in chat/email
- ❌ Use tokens with more permissions than needed
- ❌ Use the same token for multiple projects
- ❌ Store tokens in plain text files

### **If Token is Compromised**
1. **Immediately** go to GitHub → Settings → Developer settings → Personal access tokens
2. Find your token and click **Delete**
3. Create a new token following this guide
4. Update all systems with the new token

## 🔍 **Troubleshooting**

### **"Bad credentials" Error**
- Token is incorrect or expired
- Token doesn't have required permissions
- Token was deleted from GitHub

### **"Not Found" Error**
- Repository doesn't exist
- Token doesn't have access to the repository
- Repository is private but token only has public access

### **"Rate limit exceeded" Error**
- You've made too many API calls
- Wait an hour or use a different token
- Authenticated requests have higher rate limits

### **Integration Tests Failing**
- Ensure `GITHUB_TOKEN` environment variable is set
- Verify token has `repo` and `workflow` permissions
- Check token hasn't expired

## 📚 **Additional Resources**

- [GitHub PAT Documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [GitHub API Rate Limits](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting)
- [SIP Installation Guide](./installation.md)

## 🆘 **Need Help?**

If you encounter issues:
1. Check the troubleshooting section above
2. Verify your token permissions match this guide exactly
3. Test with a simple API call: `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user`
4. Create an issue in the SIP repository with error details

---

**Remember**: This token gives access to your repositories. Treat it like a password and follow security best practices!