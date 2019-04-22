###############################################################################
#
# acm_update_test.py
#
# An active cable software update test utility.
#
# usage: python build.pl -c cable_type
#   where:
#       cable_type: utt, upp or ure
#
# outputs: cable_type_build_report.txt
#
#

# region Import region
import os
import datetime
import argparse
import subprocess
import logging
import random
import string
from time import sleep
# endregion

###############################################################################
# region Global Variables region
###############################################################################

__version__ = '1.0'  # version of script

DFU_BUILD_UTILITY = 'dfu_util.pl'
DFU_BUILD_CONFIG = 'serial_number.cfg'
CABLE_VID_PIDS_DICT = {'ure': '1901:0020', 'utt': '1901:002f', 'upp12': '1901:0029'}
CABLE_DFU_VER_DICT = {'ure': '1901:0020', 'utt': 'U-TT_MT7637_V1', 'upp12': 'U-PP_MT7637_V1'}
SERIAL_NUMBER_SIZE = 100    # maximum number of characters allowed in a ACM cable
DNLD_LIST = ['BootLoader', 'COMProcessor', 'ACQProcessor']
DFU_DIRECTORY = 'none'
# endregion

###############################################################################
# region Function region
###############################################################################

def execute_command(command_list):
    try:
        command_output = subprocess.check_output(command_list)
    except subprocess.CalledProcessError as e:
        print('*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print(e.output.decode('utf-8'))
        print('ERROR during command execution, return value from command: '+str(e.returncode))
        print('*** ABORTING ***')
        print('*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        exit(e.returncode)
    except OSError as e:
        print('Error, executing command')
        print('Error string: '+e.strerror+', error number: '+e.errno)
        print('*** ABORTING ***')
        exit(-1)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        print('*** ABORTING ***')
        exit(-2)

    return command_output.decode('utf-8')

def create_serialnumber():
    """
    Create a proper random ACM serial number.
    :return: A string the meets the ACM criteria for a serial number.
    """

    serial_number_length = random.randint(1, SERIAL_NUMBER_SIZE)

    # Let's build a serial number...
    serial_number = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(serial_number_length)])
    return serial_number


def create_dfu(dfu_list):
    """
    Take the give list and build a DFU file.  The given DFU list contains the elements to build the DFU with.
    :param dfu_list:
    :return:
    """

def create_dfu_config_root(package_version, vendor_id, product_id):
    """
    Create the root block for a DFU configuration file.
    :param load_list: list of DFU load items to build list with.
    :param dfu_directory: directory to search for DFU files.
    :return:
    """
    root_list = [  # start of images list build.
        '# Root block',
        '# versions must be proper (per spec).',
        '# Note the vendor and product IDs get placed in the DFU suffix where',
        '# DFU download utilities will read them during attempted downloads.'
    ]
    root_list.append('package_version = 0x{0:08x}'.format(package_version))
    root_list.append('compatibility_version = 0x0102')
    root_list.append('vendor_id = 0x{0:04x}'.format(vendor_id))
    root_list.append('product_id = 0x{0:04x}'.format(product_id))

    return root_list


def create_dfu_config_images(load_list, dfu_directory):
    """
    Create a random DFU configuration images list.  Files names are pulled from the given directory.
    :param load_list: list of DFU load items to build list with.
    :param dfu_directory: directory to search for DFU files.
    :return:
    """
    # Build the images list...
    i = 1            # keep track of what download item we are on
    images_list = [  # start of images list build.
        '# Images block',
        '# Associate image names and image binaries.',
        '# Image name must be proper (per spec).',
        '[images]'
    ]

    for item in load_list:
        search_directory = dfu_directory+'/'+item  # build directory to search for DFU file in
        files = [f for f in os.listdir(search_directory) if os.path.isfile(search_directory+'/'+f)]  # grab all the files in the directory
        load_string = '{0:d}_{1:s} = {2:s}'.format(i, item, search_directory+'/'+random.choice(files))
        images_list.append(load_string)  # append built item
        i += 1

    return images_list


def create_dfu_config(package_version, product_id, dfu_directory):
    """
    Create a random DFU configuration file.  This will be used to build a DFU for download to a cable.
    :return:
    """
    # Build header list
    header_list = [
        '#',
        '# DFU Configuration File for active cable firmware upgrade.',
        '#',
        '# Generated on {0:s}'.format(datetime.datetime.now().isoformat()),
        '#',
        '#'
    ]

    # Build the root content
    root_list = create_dfu_config_root(package_version, 0x1901, product_id)

    # Build a random load list...
    load_list = [random.choice(DNLD_LIST) for i in range(random.randint(1, 10))]
    images_list = create_dfu_config_images(load_list, dfu_directory)

    # Concatenate everything in the right order...
    dfu_list = header_list + root_list + ['', ''] + images_list

    return dfu_list




def print_console_and_log(message):
    """
    Take the give line and send it to the console and the log file.

    Args:
        message (): The string to print to console and send to log.

    Returns:
        nothing

    """
    print(message)
    logging.info(message)



# endregion


###############################################################################
# region Main region
###############################################################################
def main(arg_list=None):
    """The main function of this module.

    Perform all the processing on a LeCroy CSV exported active cable capture.
    Returns the timing metrics on the capture data.

    """

    ###############################################################################
    # region Command line region

    ###############################################################################
    # Setup command line argument parsing...
    parser = argparse.ArgumentParser(description='ACM software download test script')
    parser.add_argument('-c', dest='cable_type',
                        help='Cable type, upp or utt or ure', required=True)
    parser.add_argument('-d', dest='dfu_directory',
                        help='Top level directory where DFU files to download reside', required=True)
    parser.add_argument('--log', dest='loglevel', default='INFO', required=False,
                        help='logging level for log file')
    parser.add_argument('-v', dest='verbose', default=False, action='store_true',
                        help='verbose output flag', required=False)
    parser.add_argument('--version', action='version', help='Print version.',
                        version='%(prog)s Version {version}'.format(version=__version__))

    # Parse the command line arguments
    args = parser.parse_args(arg_list)


    ###############################################################################
    # Setup logging...
    getattr(logging, args.loglevel.upper())
    numeric_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.loglevel)
    log_format = '%(asctime)s:%(levelname)s:[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s'
    logging.basicConfig(filename='acm_update_test.log', level=numeric_level, format=log_format)

    # Test the cable type.
    cable_type = args.cable_type
    if cable_type not in CABLE_VID_PIDS_DICT:
        # print_console_and_log('Bad cable type given: '+cable_type+' should be one of '+CABLE_VID_PIDS_DICT.keys())
        print('Bad cable type given: '+cable_type+' should be one of '+str(list(CABLE_VID_PIDS_DICT.keys())))
        exit(-1)

    # Test existence of DFU top level directory
    if os.path.isdir(args.dfu_directory) is False:
        print('ERROR, ' + args.dfu_directory + ' is not a directory')
        print('\n\n')
        exit(-1)

    DFU_DIRECTORY = args.dfu_directory

    # endregion

    for i in range(100):
        serial_number = create_serialnumber()   # make an ACM serial number

        ################################################################################################################
        # build a serial number DFU
        print('')
        print('Programming cable with serial number: '+serial_number)
        dfu_filename = 'sn_'+cable_type+'_'+serial_number+'.dfu'
        command_to_execute=['perl', DFU_BUILD_UTILITY, '-s '+serial_number, '-a'+cable_type, '-o '+dfu_filename, '-v']
        command_result_string = execute_command(command_to_execute)

        # If verbose, print command and command results...
        if args.verbose is True:
            print('')
            print('*************************************************')
            print('Command : '+str(command_to_execute))
            print('command_result_string :'+str(command_result_string))
            print('')

        ################################################################################################################
        # Program the ACM with that serial number
        command_to_execute = ['dfu-util',
            '-d '+CABLE_VID_PIDS_DICT[cable_type]+','+CABLE_VID_PIDS_DICT[cable_type],
            '-D'+dfu_filename]
        command_result_string = execute_command(command_to_execute)


        # If verbose, print command and command results...
        if args.verbose is True:
            print('')
            print('*************************************************')
            print('Command : '+str(command_to_execute))
            print('command_result_string :'+str(command_result_string))
            print('')

        print('Sleeping...')
        sleep(5)    # wait for cable to reset and enumerate...

        print('Testing cable for expected serial number')

        ################################################################################################################
        # Get enumeration info of just programmed cable...
        command_to_execute = ['lsusb', '-v', '-d '+CABLE_VID_PIDS_DICT[cable_type]]
        command_result_string = execute_command(command_to_execute)

        # If verbose, print command and command results...
        if args.verbose is True:
            print('')
            print('*************************************************')
            print('Command : '+str(command_to_execute))
            print('command_result_string :'+str(command_result_string))
            print('')

        ################################################################################################################
        # Create list of string from lsusb output.
        lsusb_list = [s.strip() for s in command_result_string.splitlines()]

        ################################################################################################################
        # Get the string description we are interested in...
        string_descriptor_list = [s for s in lsusb_list if s.startswith('iManufacture') or
             s.startswith('iProduct') or
             s.startswith('iSerial')]

        # Verify we got 3 hits...
        if len(string_descriptor_list) != 3:
            # We did not get 3 hits as expected, something is wrong...
            print('Did NOT find iManufacture or iProduct or iSerial in lsusb output')
            print('Found this: ', str(string_descriptor_list))
            exit()

        # Verify iManufacture is correct...
        manfac = string_descriptor_list[0].split()
        if manfac[0] != 'iManufacturer' or manfac[1] != '1' or manfac[2] != 'GE' or manfac[3] != 'Healthcare':
            print('String descriptor iManufacturer does not match expected')
            print(str(manfac))
            exit(1)

        # Verify iProduct is correct...
        product = string_descriptor_list[1].split()
        if product[0] != 'iProduct' or product[1] != '2' or product[2] != CABLE_DFU_VER_DICT[cable_type]:
            print('String descriptor iProduct does not match expected')
            print(str(product))
            exit(1)

        # Verify iSerial is correct...
        serial = string_descriptor_list[2].split()
        if serial[0] != 'iSerial' or serial[1] != '3' or serial[2] != serial_number:
            print('String descriptor iSerial does not match expected')
            print(str(serial))
            print('Expected serial number : '+serial_number)
            exit(1)

        # Remove the serial number DFU...
        print('`PASS')
        os.remove(dfu_filename)

    print('**************** ALL PASS ****************')
    return 0

# endregion

###############################################################################


if __name__ == '__main__':
    rv = main()

    exit(rv)
