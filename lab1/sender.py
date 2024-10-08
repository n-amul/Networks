import socket
import struct
import os
import time
import argparse

"""Receives request from the Requester for the filename (from which data is to be sent)"""
def receive_request(UDP_IP, UDP_PORT):
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
		sock.bind(('0.0.0.0', UDP_PORT))

		while True:
			data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
			packet_type = data[0:1].decode('utf-8')
			header = data[1:9]
			header = struct.unpack('II', header)
			sequence_number_network = header[0]
			sequence_number = socket.ntohl(sequence_number_network)
			packet_length = header[1]

			print("Packet type:     %s"% packet_type)
			print("Sequence no.:    %d" % sequence_number)
			filename = data[9:].decode('utf-8')
			print("Payload:         %s "% filename)
			print("\n")

			sock.close()
			return packet_type, filename, addr
	except Exception as ex:
		raise ex


def create_header(packet_type, sequence_number, payload_length):
	sequence_number_network = socket.htonl(sequence_number)
	header = str(packet_type).encode("utf-8") + struct.pack('II', sequence_number_network, payload_length)
	return header


def send_packets(packet_type, requester_addr, requestor_wait_port, sequence_number, payload_length, rate, message):
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		if packet_type == "D" and message != "":
			chunks = [message[i:i + payload_length] for i in range(0, len(message), payload_length)]

			for i in chunks:
				header = create_header(packet_type, sequence_number, len(i))
				sock.sendto((header + i.encode("utf-8")), (requester_addr, requestor_wait_port))
				current_time = time.time()
				milliseconds = int((current_time - int(current_time)) * 1000)

				print("DATA Packet")
				print(f"Send Time:          {time.strftime('%Y-%m-%d %H:%M:%S')}.{milliseconds:03d}")
				print(f"Requester Addr:     {requester_addr}:{requestor_wait_port}")
				print(f"Seq No:             {sequence_number}")
				print(f"Length:             {len(i)}")
				print(f"Payload:            {i[9:9+4]}")
				print("\n")

				sequence_number = sequence_number + len(j)
				time.sleep(1/rate)

		end_header = create_header('E', sequence_number, 0)
		sock.sendto(end_header + str(0).encode("utf-8"), (requester_addr, requestor_wait_port))

		current_time = time.time()
		milliseconds = int((current_time - int(current_time)) * 1000)
		print("END Packet")
		print(f"Send Time:          {time.strftime('%Y-%m-%d %H:%M:%S')}.{milliseconds:03d}")
		print(f"Requester Addr:     {requester_addr}:{requestor_wait_port}")
		print(f"Seq No:             {sequence_number}")
		print(f"Length:             {0}")
		print(f"Payload:            {0}")
		print("\n")
	except Exception as ex:
		raise ex


def main(sender_wait_port, requestor_port, packet_rate, start_seq_no, payload_length):
	packet_type, filename, client_address = receive_request(socket.gethostbyname(socket.gethostname()), sender_wait_port)
	print("Requestor waits on IP: %s" % client_address[0])
	print("Sender waiting on port: %s \n" % sender_wait_port)
	if packet_type == 'R':
		if os.path.exists(filename):
			with open(filename, "rb") as fd:
				message = fd.read().decode("utf-8")
				# Client address is combination of IP Address and port
				send_packets('D', client_address[0], requestor_port, start_seq_no, payload_length, packet_rate, str(message))
		else:
			print("File with name {} does not exist. Ending the connection.\n".format(filename))
			send_packets('E', client_address[0], requestor_port, start_seq_no, payload_length, packet_rate, "")


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Sends chunks of a file to the requester")
	parser.add_argument("-p", "--port", dest='port', type=int, required=True, help="Port number on which the sender waits for request")
	parser.add_argument("-g", "--req-port", dest="requestor_port", type=int, required=True, help="Port number on which the requestor is waiting")
	parser.add_argument("-r", "--rate", dest='rate', type=int, required=True, help="Rate of packets per sec to send")
	parser.add_argument("-q", "--seq-no", dest="start_seq_no", type=int, required=True, help="Initial sequence number of the package exchange")
	parser.add_argument("-l", "--length", dest="payload_length", type=int, required=True, help="Length of the payload in the packets (in bytes)")

	args = parser.parse_args()
	for port_numbers in [args.port, args.requestor_port]:
		if port_numbers not in range(2050, 65536):
			raise Exception("Port number should be in the range 2050 to 65535. Passed: {}".format(port_numbers))
	main(args.port, args.requestor_port, args.rate, args.start_seq_no, args.payload_length)

