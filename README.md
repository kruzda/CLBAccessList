#Manage CLB Access List

This script was initialy written with the intention of being a fail2ban action.

I was getting a lot of POST requests to wp-login.php and I wanted fail2ban to block the IP addresses on a LB level.

```text
Usage: ./accessListTool.py [--list] [--delete-everything] | [--add] [--delete] <123.45.67.89>
-a|-A|--add <IP Address>         - Add an IP address to your load balancers Access List.
-d|-D|--delete <IP address>      - Remove an IP address to your load balancers Access List.
-l|-L|--list                     - Shows the current accesslist.
-rmrf|-RMRF|--delete-everything  - Deletes the entire accesslist.
-h|-H|--help                     - Show help dialog.
```

I've added a few extra options to manage all access list operations.


# Protecting Wordpress

If you'd like to protect wordpress from bruteforce attacks on wp-login.php and pingback requests, follow the below guide.

###Step 1
- Install [WP-fail2ban](https://wordpress.org/plugins/wp-fail2ban/)

Install this via the dashboard and set it to active.

###Step 2
- Edit wp-config.php file with the below lines:

```php
define('WP_FAIL2BAN_AUTH_LOG',LOG_AUTHPRIV);
define('WP_FAIL2BAN_LOG_PINGBACKS',true);
define('WP_FAIL2BAN_PROXIES','127.0.0.1');
```
**Note, you may need to change 127.0.0.1 / add additonal IP addresses**
**The idea here is to list the IP addresses of the trusted proxies that will appear as the remote IP for the request. When defined:**
* If the remote address appears in the `WP_FAIL2BAN_PROXIES` list, *WPf2b* will log the IP address from the `X-Forwarded-For` header.
* If the remote address does not appear in the `WP_FAIL2BAN_PROXIES` list, *WPf2b* will return a 403 error.
* If there's no X-Forwarded-For header, *WPf2b* will behave as if `WP_FAIL2BAN_PROXIES` isn't defined.

###Step 3 
- Configure fail2ban

  - Configure a filter | **_This tails fail2ban what to look for in a log file_**
    - Copy [wordpress.conf](filter.d/wordpress.conf) to /etc/fail2ban/filter.d/wordpress.conf. **_This file exists in the plugin direcotry but I have included here for ease._**

  - Configure an action | **_This tells fail2ban what to do when it finds something in the log_**
    - Copy [rackspace-lb.conf](action.d/rackspace-lb.conf) to /etc/fail2ban/action.d/rackspace-lb.conf**Make sure accessListTool.py is executable, located in /usr/local/bin/ and updated with your credentials**

  - Create the jail | **_This tells fail2ban the criteria for setting a ban_**
    - Copy [wordpress-jail.conf](jail.d/wordpress-jail.conf) to /etc/fail2ban/jail.d/wordpress-jail.conf

  - Restart fail2ban
    - service fail2ban restart 

We've not configured Wordpress to block any IP address which fails to login / sends a XMLRPC pingback more than 3 times within 2 minutes. The ban will last an hour by default.

**Note This was tested on Ubuntu 14.04 / fail2ban v0.8.11. This was tested on a setup with only one Website - this may have a negative impact on servers hosting more than one Wordpress site - will look for ways to combat this in the future**

-Blake
