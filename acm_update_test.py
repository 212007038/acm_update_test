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
SERIAL_NUMBER_SIZE = 100    # maximum number of characters allowed in a ACM cable
DNLD_LIST = ['BootLoader', 'DFU', 'COMProcessor', 'ACQProcessor']
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

def build_dfu(dfu_list):
    """
    Take the give list and build a DFU file.  The given DFU list contains the elements to build the DFU with.
    :param dfu_list: 
    :return:
    """

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
    parser.add_argument('-c', dest='cable_type', help='Cable type, upp or utt or ure', required=True)
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

    # endregion

    for i in range(100):
        serial_number = create_serialnumber()   # make an ACM serial number

        ################################################################################################################
        # build a serial number DFU
        dfu_filename = 'sn_'+cable_type+'_'+serial_number+'.dfu'
        command_to_execute=['perl', DFU_BUILD_UTILITY, '-s '+serial_number, '-a'+cable_type, '-o '+dfu_filename, '-v']
        print('Command: '+str(command_to_execute))
        command_result_sting = execute_command(command_to_execute)

        print('The Serial number is: '+serial_number)
        print('Command results was: '+command_result_sting)

        ################################################################################################################
        # Program the ACM with that serial number
        command_to_execute = ['dfu-util', '-v',
            '-d '+CABLE_VID_PIDS_DICT[cable_type]+','+CABLE_VID_PIDS_DICT[cable_type],
            ' -D '+dfu_filename]
        command_result_sting = execute_command(command_to_execute)

        print('Command results was: '+command_result_sting)

        sleep(5)    # wait for cable to reset and enumerate...

        ################################################################################################################
        # Get enumeration info of just programmed cable...
        command_to_execute = ['lsusb', '-v', '-d '+CABLE_VID_PIDS_DICT[cable_type]]
        command_result_sting = execute_command(command_to_execute)

        ################################################################################################################
        # and verify the serial number reported by the cable matches what was programmed...


        '''
        # Verify the serial number was programmed into the cable.
        command_result_sting = execute_command(['lsusb', '-v', '-d '+CABLE_VID_PIDS_DICT[cable_type]])

        # Attempt to capture all 3 string descriptor.
        lsusb_output = [s.strip() for s in command_result_sting.splitlines()]
        string_descriptors = [s for s in lsusb_output if s.startswith('iManufacture') or
             s.startswith('iProduct') or
             s.startswith('iSerial')]

        # Verify we got 3 hits...
        if len(string_descriptors) != 3:
            # We did not get 3 hits as expected, something is wrong...
            print('Did NOT find iManufacture or iProduct or iSerial in lsusb output')
            print('Found this: ', string_descriptors)
            exit()
        '''


        # Verify iManufacture is correct...

        # Verify iProduct is correct...

        # Verify iSerial is correct...




    return 1

# endregion

###############################################################################


if __name__ == '__main__':
    rv = main()

    exit(rv)