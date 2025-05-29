# Signal Sources Configuration Guide

This guide explains how to configure signal sources to automatically route trading signals from WhatsApp (and future platforms) to your trading accounts.

## Overview

The signal sources feature allows you to:
- Create unique webhook URLs for each WhatsApp channel/phone number
- Filter messages by specific WhatsApp groups or chats
- Route signals to multiple trading accounts automatically
- Auto-approve signals for specific accounts (e.g., paper trading)

## Setting Up a WhatsApp Source

### 1. Create a Signal Source

1. Go to **Settings** → **Signal Sources**
2. Click **Add Source**
3. Fill in the form:
   - **Source Type**: Select "WhatsApp (WHAPI)"
   - **Channel/Instance Name**: A descriptive name (e.g., "My Trading Phone")
   - **Display Name**: What you'll see in the app (e.g., "Trading Signals Group")
   - **Description**: Optional details about this source
   - **Chat ID Filter**: (Optional) Specific WhatsApp chat/group ID to monitor
   - **Route Signals to Accounts**: Select which accounts should receive signals
   - **Auto-approve**: Check this for accounts where signals should be auto-approved

### 2. Configure WHAPI Webhook

After creating a source, you'll see a unique webhook URL like:
```
https://your-app.com/api/webhook/whapi/YOUR_UNIQUE_TOKEN
```

1. Copy this webhook URL using the copy button
2. Go to your WHAPI dashboard
3. Navigate to your channel settings
4. Add this webhook URL to receive messages
5. Save the webhook configuration

### 3. Chat ID Filtering (Optional)

To only process messages from a specific WhatsApp group or chat:

1. Find the chat ID in WHAPI (usually looks like `120363123456789012@g.us` for groups)
2. Enter this in the "Chat ID Filter" field when creating/editing the source
3. Only messages from this specific chat will be processed

## How It Works

### Message Flow

1. **WhatsApp Message** → Sent in a group/chat
2. **WHAPI** → Receives message and sends to your webhook URL
3. **Your App** → Identifies the source by webhook token
4. **Chat Filter** → Checks if message is from the configured chat (if filter is set)
5. **AI Analysis** → Extracts trading signals from the message
6. **Signal Creation** → Creates signals for all configured accounts
7. **Auto-Approval** → Automatically approves signals for configured accounts

### Multiple Channels/Phones

You can create multiple sources for different scenarios:

- **Different Phone Numbers**: Each WhatsApp Business account gets its own source
- **Different Groups**: Use chat ID filters to monitor specific groups
- **Different Routing**: Route signals from different sources to different accounts

### Example Scenarios

#### Scenario 1: Paper and Live Trading
- Create one source for your trading signals group
- Route to both paper and live accounts
- Enable auto-approve for paper account only
- Result: Paper trades execute automatically, live trades need approval

#### Scenario 2: Multiple Signal Providers
- Create separate sources for each signal provider's WhatsApp group
- Use chat ID filters to ensure proper separation
- Route each to different accounts or strategies
- Track performance per signal provider

#### Scenario 3: Testing New Strategies
- Create a source for a new signal group
- Route only to a paper trading account with auto-approve
- Monitor performance before enabling live trading

## Security Considerations

1. **Unique Webhooks**: Each source has a unique, random webhook URL
2. **No Cross-Contamination**: Messages sent to one webhook won't affect other sources
3. **User Isolation**: Sources are user-specific - other users can't see your sources
4. **Chat Filtering**: Additional security by only processing specific chats

## Troubleshooting

### Messages Not Being Received
1. Check if the source is "Active" in settings
2. Verify the webhook URL is correctly configured in WHAPI
3. Check webhook logs in WHAPI dashboard
4. Ensure your accounts are active

### Wrong Chat Messages Being Processed
1. Add a chat ID filter to the source
2. Find the chat ID in WHAPI message details
3. Update the source with the correct chat ID

### Signals Not Created for All Accounts
1. Verify all target accounts are active
2. Check if accounts are properly linked to the source
3. Ensure the user has access to all linked accounts

## Future Enhancements

- **Telegram Support**: Coming soon with similar webhook functionality
- **Discord Support**: Planned for future releases
- **Keyword Filtering**: Filter signals by specific keywords
- **Time-based Filtering**: Only process signals during market hours
- **Risk Management**: Set position size limits per source 