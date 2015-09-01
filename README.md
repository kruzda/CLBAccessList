# Manage CLB Access List

This script was initialy written with the intention of being a fail2ban action.

I was getting a lot of POST requests to wp-login.php and I wanted fail2ban to block the IP addresses on a LB level.

Now I've added options for deleting everything and showing the current list.

```text
Usage: ./accessListTool.py [--list] [--delete-everything] | [--add] [--delete] <123.45.67.89>
-a|-A|--add <IP Address>         - Add an IP address to your load balancers Access List.
-d|-D|--delete <IP address>      - Remove an IP address to your load balancers Access List.
-l|-L|--list                     - Shows the current accesslist.
-rmrf|-RMRF|--delete-everything  - Deletes the entire accesslist.
-h|-H|--help                     - Show help dialog.
```
