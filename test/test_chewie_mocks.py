"""Unittests for chewie/chewie.py"""

from collections import namedtuple

import unittest
from unittest.mock import patch, Mock

from chewie.chewie import Chewie
from chewie.event import EventMessageReceived

def return_if(expected, return_value):
    """allows us to do expect-this-return-that style mocking"""
    def inner_function(*args):
        """workaround to effectively give us an anonymous function"""
        if args == expected:
            return return_value
        raise Exception("Expected %s but got %s" % (expected, args))

    return inner_function

FakeLogger = namedtuple('FakeLogger', ('name',)) # pylint: disable=invalid-name
FakeEapMessage = namedtuple('FakeEapMessage', ('src_mac',)) # pylint: disable=invalid-name

class ChewieWithMocksTestCase(unittest.TestCase):
    """Main chewie.py test class"""

    def setUp(self):
        self.chewie = Chewie('lo', FakeLogger('logger name'),
                             None, None, None,
                             '127.0.0.1', 1812, 'SECRET',
                             '44:44:44:44:44:44')

    @patch("chewie.chewie.Chewie.running", Mock(side_effect=[True, False]))
    @patch("chewie.chewie.MessageParser.ethernet_parse")
    @patch("chewie.chewie.FullEAPStateMachine")
    @patch("chewie.chewie.sleep", Mock())
    def test_eap_packet_in_goes_to_new_state_machine(self, state_machine, ethernet_parse): #pylint: disable=invalid-name
        """test EAP packet creates a new state machine and is sent on"""
        self.chewie.eap_socket = Mock(**{'receive.return_value': 'message from socket'})
        ethernet_parse.side_effect = return_if(
            ('message from socket',),
            (FakeEapMessage('fake src mac'), 'fake dst mac')
            )
        self.chewie.receive_eap_messages()
        state_machine().event.assert_called_with(
            EventMessageReceived(FakeEapMessage('fake src mac'), 'fake dst mac')
            )

    @patch("chewie.chewie.Chewie.running", Mock(side_effect=[True, False]))
    @patch("chewie.chewie.MessagePacker.ethernet_pack")
    @patch("chewie.chewie.sleep", Mock())
    def test_eap_output_packet_gets_packed_and_sent(self, ethernet_pack): #pylint: disable=invalid-name
        """test EAP packet creates a new state machine and is sent on"""
        self.chewie.eap_socket = Mock()
        ethernet_pack.return_value = "packed ethernet"
        self.chewie.eap_output_messages.put(["output eap message", "src mac", "port mac"])
        self.chewie.send_eap_messages()
        self.chewie.eap_socket.send.assert_called_with("packed ethernet")

    @patch("chewie.chewie.Chewie.running", Mock(side_effect=[True, False]))
    @patch("chewie.chewie.MessageParser.radius_parse")
    @patch("chewie.chewie.FullEAPStateMachine")
    @patch("chewie.chewie.sleep", Mock())
    def test_radius_packet_in_goes_to_state_machine(self, state_machine, radius_parse): #pylint: disable=invalid-name
        """test radius packet goes to a state machine"""
        # note that the state machine has to exist already - if not then we blow up
        self.chewie.radius_socket = Mock(**{'receive.return_value': 'message from socket'})
        #self.chewie.radius_secret = 'it\'s a secret'
        # not checking args as we can't mock the callback
        self.chewie.receive_radius_messages()
        state_machine().event.assert_called_with(
            EventMessageReceived(FakeRadiusMessage('fake src mac'))
            )
