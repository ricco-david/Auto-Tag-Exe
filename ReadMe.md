# Auto Message Scheduler - Tutorial

## Overview
Auto Message Scheduler is a desktop application that helps you automatically process and respond to messages from Facebook Pages. It can search through conversations, find specific phone numbers, and send automated replies.

## Features
- Process all Facebook Pages associated with your account
- Search for specific phone numbers in conversations
- Send automated replies to matching conversations
- Schedule tasks for later execution
- Real-time progress tracking
- Detailed logging system

## Getting Started

### Prerequisites
1. A Facebook Page access token
2. The phone numbers you want to search for
3. The message you want to send as an auto-reply

### Step-by-Step Guide

1. **Launch the Application**
   - Double-click the `auto-message.exe` file
   - The main window will open with the task configuration form

2. **Configure Your Task**
   - **Access Token**: Enter your Facebook Page access token
   - **Custom Message**: Type the message you want to send as an auto-reply
   - **Phone Numbers**: Enter the phone numbers to search for (separate multiple numbers with commas)
   - **Date Range**: Select the date range for searching conversations
     - Since Date: Start date for the search
     - Until Date: End date for the search

3. **Execution Mode**
   - **Run Immediately**: Starts the task right away
   - **Schedule for Later**: Schedules the task for a later time

4. **Submit the Task**
   - Click the "Submit" button to start or schedule the task
   - The task will appear in the "Active Tasks" table
   - Progress and status will be shown in real-time

5. **Monitor Progress**
   - Watch the "Terminal Log" section for detailed information
   - Check the "Active Tasks" table for task status
   - Progress percentage will be updated automatically

## Understanding the Interface

### Task Configuration Form
- **Process All Pages**: Checkbox to process all available pages
- **Access Token**: Your Facebook Page access token
- **Custom Message**: The auto-reply message
- **Phone Numbers**: Target phone numbers to search for
- **Date Range**: Time period for conversation search

### Active Tasks Table
Shows all running and scheduled tasks with:
- Process ID
- Page ID
- Message Preview
- Phone Count
- Date Range
- Status
- Progress

### Terminal Log
Displays real-time information about:
- Task progress
- Found conversations
- Matched phone numbers
- Auto-reply status
- Any errors or warnings

## Tips for Best Results

1. **Access Token**
   - Make sure your access token is valid and has necessary permissions
   - Keep your access token secure

2. **Phone Numbers**
   - Enter phone numbers in international format (e.g., +1234567890)
   - Separate multiple numbers with commas
   - Include country code for better matching

3. **Date Range**
   - Choose a reasonable date range to avoid processing too many conversations
   - Consider timezone differences

4. **Custom Message**
   - Keep messages clear and professional
   - Test your message before scheduling

## Troubleshooting

### Common Issues
1. **No Pages Found**
   - Check if your access token is valid
   - Verify you have access to the pages

2. **No Conversations Found**
   - Verify the date range
   - Check if there are conversations in the selected period

3. **Auto-reply Not Sent**
   - Check if the phone numbers match
   - Verify message format
   - Check access token permissions

### Getting Help
If you encounter any issues:
1. Check the terminal log for error messages
2. Verify all input fields are correctly filled
3. Ensure your access token has necessary permissions

## Version Information
Current Version: V1.0.2