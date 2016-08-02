# Title: data_generator.py
# Usage: data_generator.py <input_file> <num_of_lines> <file_type> <output_file>
# Revision: 0.9.1
# Python version: 3.x
# Author: Chalmer Lowe
# Date: 20150121
# Description: This script generates various files with random/semi-random
#              data for use in classes and demonstrations.
#
# TODO:
#   2) improve commenting so that the functions have built-in help
#   3) enable an option such that the user can skip writing a full-blown file
#      and can instead write just a certain set of columns
#      i.e. can choose just name, or just name, email, lat & long columns
#   4) provide an option to include a header row
#   5) improve the usage component to produce a help file
#   6) set up outputs for other file types...
#      * json
#      * xml
#      * pickle
#   7) add more columns?
#      * to/fm mac addr - need to consider pairing to ips?
#      * payload size (0-1000000) # FUNC is complete, not integrated yet.
#      * user agent string - need to consider pairing to ips?
#        > browser
#        > windows/mac/linux
#        > version
#   8) add an option to include/exclude corrupted data
#      * corrupted data -> NULL, blank lines, random gobbledy-gook
#      * enable the inclusion of some/all
#      * enable the use of threshholds: very corrupted/limited corruption
#   9) add an option to set the delimiter AND/OR include quoting

import sys
from random import choice, randint, random, uniform
import datetime
from datetime import datetime as dt
from collections import defaultdict
from os.path import basename

MAX_N_PAYLOAD_BYTES = 10**6

def get_usage():
    program_name = basename(sys.argv[0])
    return '''
    {program_name} produces data in multiple formats,
    including sql tables and CSVs.
    Usage: {program_name} <input_file> <num_of_lines> <file_type> <out_file>
    '''.format(program_name=program_name)


def complain_and_quit(error_message=None):
    messages = []
    if error_message:
        messages.append('ERROR: %s' % error_message)
    messages.append(get_usage())
    s = '\n'.join(messages)
    sys.exit(s)


def create_email_address(first_name, last_name, domain):
    '''Creates an email address in the format first initial last name @ domain
    for example:
    bwayne@batman.org
    '''
    email_address = '{}{}@{}'.format(first_name[0], last_name, domain)
    return email_address


def make_random_ipv4_address():
    '''Returns random IPV4 address in "dotted quad" formatted string.
    Each byte of IPV4 address can be 1 to 255 inclusive.
    E.g., '191.158.12.3'.'''

    octets = (str(randint(1, 0x100-1)) for _ in range(4))
    dotted_quad_ipv4_address = '.'.join(octets)
    return dotted_quad_ipv4_address


def make_random_ipv4_addresses(n):
    '''Returns list of n random IPV4 addresses in "dotted quad"
    formatted strings.'''

    return [make_random_ipv4_address() for _ in range(n)]


def create_payload_size(n):
    '''Generates a random payload size for the communication session.
    Ranges from 1 byte to n+1 bytes
    '''
    size = randint(1, n)
    return size


def get_random_time_increment():
    '''Returns a random datetime.timedelta() value
    for 1 to 99 seconds forward
    plus 1 in 6 chance of going back one day.
    '''
    delta_days = (-1, 0, 0, 0, 0, 0)  # Picking an item from this at random
                                      # for the days argument
                                      # to datetime.timedelta
                                      # gives backwards shift of 1 day
                                      # with a 1 out of 6 chance.
                                      # Add/remove zeroes to change this.
    increment = datetime.timedelta(choice(delta_days), randint(1, 100-1))
    return increment


def format_latlong(x, is_latitude):
    if False:  # This is the fancy way.
        FORMAT = '{:.5f} {}'
        if is_latitude:
            "+45.123456 becomes '45.12346 N'."
            "-45.123456 becomes '45.12346 S'."
            assert -90. <= x <= 90.
            direction = 'N' if x >=0 else 'S'
            x = abs(x)
        else:
            "+83.1234567 becomes '83.12346 E'."
            "-83.1234567 becomes '83.12346 W'."
            x %= 360.
            if x > 180.:
                x = 360. - x
                direction = 'W'
            else:
                direction = 'E'
    else:  # Old way.
        FORMAT = '{:.5f}'
        direction = None

    return FORMAT.format(x, direction)

def geo(min_lat, max_lat, min_long, max_long):
    '''creates a pair of numbers that simulate a geo-location with
    latitude and longitude based on the decimal degrees format:
    40.446 N 79.982 W
    For purposes of generating 'bounding box' puzzles/problems, this generator
    can output geos within a 'large' bounding box enabling a smaller
    bounding box to be selected out of the broader range of geos as part of the
    puzzle.
    '''
    latitude = uniform(min_lat, max_lat)
    formatted_latitude = format_latlong(latitude, True)

    longitude = uniform(min_long, max_long)
    formatted_longitude = format_latlong(longitude, False)

    return formatted_latitude, formatted_longitude


def create_outputs(num_of_lines, names, ip_addresses, bounding_box, end='\n'):
    curr_time = dt.now()
    outputs = []
    for line in range(num_of_lines):
        # generate a new line by calling all the appropriate funcs
        # and gathering the results into an output line

        name = choice(list(names.keys()))
        email = names[name]
        fmip = choice(ip_addresses)
        toip = choice(ip_addresses)
        tstamp = curr_time.strftime('%Y-%m-%dT%H:%M:%S')
        lat, long = geo(*bounding_box)
        # print(name, email, fmip, toip, tstamp, lat, long)    #dbg
        output = ','.join([name, email, fmip,
                           toip, tstamp, lat, long]) + end
        time_inc = get_random_time_increment()
        curr_time += time_inc
        outputs.append(output)
    return outputs


def main():
    try:
        input_file, num_of_lines, file_type, out_file = sys.argv[1:4+1]
    except ValueError:
        complain_and_quit('Wrong number of arguments.')

    try:
        num_of_lines = int(num_of_lines)
    except ValueError:
        complain_and_quit(
            "num_of_lines argument was '%s' instead of integer." %
            num_of_lines)

    with open(input_file) as f:
        domain = f.readline().strip()

        names = defaultdict(str)

        for line in f:
            line = line.strip()
            first_name, last_name = line.split(' ')
            names[line] = create_email_address(first_name, last_name, domain)

    ip_addresses = make_random_ipv4_addresses(30)

    # The lat longs below create a bounding box around Liechtenstein
    # (why?, because!)
    # 47.141667, 9.523333

    min_lat = 45
    max_lat = 50
    min_long = 7.5
    max_long = 12.5
    if False:  # Handy for testing.
        min_lat = -90.
        max_lat = +90.
        min_long = -180.
        max_long = +180.
    bounding_box = (min_lat, max_lat, min_long, max_long)

    if file_type == 'csv':
        with open(out_file, 'w') as fout:
            outputs = create_outputs(num_of_lines, names, ip_addresses, bounding_box)
            print('Output length (csv):', len(outputs))
            for line in outputs:
                fout.write(line)
        fout.close()

    elif file_type == 'sql':
        import sqlite3 as sql
        conn = sql.connect(out_file)
        cur = conn.cursor()
        try:
            cur.execute('''CREATE TABLE superheroes (name text,
                                                     email text,
                                                     fmip text,
                                                     toip text,
                                                     datetime text,
                                                     lat text,
                                                     long text)''')
        except:
            pass

        outputs = create_outputs(num_of_lines, names, ip_addresses, bounding_box, end='')
        print('Output length (sql):', len(outputs))
        for line in outputs:
            name, email, fmip, toip, datetime, lat, long = line.split(',')
            cur.execute('''INSERT INTO superheroes VALUES (?, ?, ?, ?, ?, ?, ?)''',
                       (name, email, fmip, toip, datetime, lat, long))
        conn.commit()
        for n, l in cur.execute('''SELECT name, lat FROM superheroes LIMIT 200'''):
            print(n, l)
        conn.close()

if __name__ == '__main__':
    main()
