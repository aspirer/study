#include <rados/librados.h>
#include <rbd/librbd.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>

static int tx = 0;
static int rx = 0;

static int stop = 0;

void sig_handler(int signo)
{
    if (signo == SIGINT || signo == SIGTERM) {
      printf("received SIGINT/SIGTERM\n");
      stop = 1;
    }
}


rados_t init_rados() {
    // we will use all of these below
    int ret = 0;
    rados_t rados = NULL;

    // 1. init rados object
    ret = rados_create(&rados, "admin"); // just use the client.admin keyring
    if (ret < 0) { // let's handle any error that might have come back
        printf("couldn't initialize rados! err %d\n", ret);
        return NULL;
    } else {
        printf("inited rados cluster object\n");
    }
    return rados;
}

rados_ioctx_t init_ioctx(rados_t rados, const char* pool) {
    int ret = 0;
    rados_ioctx_t io_ctx = NULL;

    // 2. read ceph config file
    ret = rados_conf_read_file(rados, "./ceph.conf");
    if (ret < 0) {
        // This could fail if the config file is malformed, but it'd be hard.
        printf("failed to parse config file! err %d\n", ret);
        return NULL;
    }

    // 3. connect to ceph cluster
    ret = rados_connect(rados);
    if (ret < 0) {
        printf("couldn't connect to cluster! err %d\n", ret);
        return NULL;
    } else {
        printf("connected to the rados cluster\n");
    }

    // 4. init io context for rbd pool
    ret = rados_ioctx_create(rados, pool, &io_ctx);
    if (ret < 0) {
        printf("couldn't setup ioctx! err %d\n", ret);
        rados_shutdown(rados);
        return NULL;
    } else {
        printf("created an ioctx for pool: %s\n", pool);
    }

    return io_ctx;
}

rbd_image_t init_image(rados_ioctx_t io_ctx, const char * vol) {
    int ret = 0;

    // 5. open rbd image
    rbd_image_t image;
    ret = rbd_open(io_ctx, vol, &image, NULL);
    if (ret < 0) {
        printf("couldn't open rbd image! err %d\n", ret);
        return NULL;
    } else {
        printf("opened an rbd image: %s\n", vol);
    }

    return image;
}

uint64_t get_rbd_size(rbd_image_t image) {
    int ret = 0;
    uint64_t size = 0;

    // 6. get rbd image size
    ret = rbd_get_size(image, &size);
    if (ret < 0) {
        printf("couldn't get image size! err %d\n", ret);
        return EXIT_FAILURE;
    } else {
        printf("The size of the image is: %dMB\n", size/1024/1024);
    }

    return size;
}

void rbd_finish_aiocb(rbd_completion_t c, void *arg)
{
    // int ret = rbd_aio_wait_for_complete(c);
    ++rx;
    int ret = rbd_aio_get_return_value(c);
    rbd_aio_release(c);

    // for aio read callback, the read data should be copied here to caller
    //printf("aio callback count: %d\n", rx);
}

int aio_write(rbd_image_t image, const char *buff, int len, uint64_t offset) {
    rbd_completion_t c;
    int ret = rbd_aio_create_completion((void *)buff, (rbd_callback_t) rbd_finish_aiocb, &c);
    if (ret < 0) {
        printf("create callback failed %s\n", ret);
        return ret;
    }

    ret = rbd_aio_write(image, offset, len, buff, c);
    if (ret < 0) {
        printf("write to image failed %s\n", ret);
        return ret;
    }
    //printf("write %d bytes to image end\n", len);

    return ret;
}

/*
int aio_read(rbd_image_t image, char *buff) {
    int off = 128;
    int len = 10;
    rbd_completion_t c;
    int ret = rbd_aio_create_completion(buff, (rbd_callback_t) rbd_finish_aiocb, &c);
    if (ret < 0) {
        printf("create callback failed %s\n", ret);
        return ret;
    }
    memset(buff, 0, 128);
    ret = rbd_aio_read(image, off, len, buff, c);
    if (ret < 0) {
        printf("read from image failed %s\n", ret);
        return ret;
    }
    printf("read from image end\n");

    return ret;
}
*/

int main(int argc, char *argv[]) {
    if (argc < 4) {
        printf("Usage: %s <pool> <volume> <delay>\n", argv[0]);
        return -1;
    }

    if (signal(SIGINT, sig_handler) == SIG_ERR || signal(SIGTERM, sig_handler) == SIG_ERR) {
        printf("\ncan't catch SIGINT\n");
        return -2;
    }

    int ret, delay, len;
    uint64_t offset;
    char buff[4096] = {0};
    char pool[32] = {0};
    char vol[32] = {0};

    rados_t rados = init_rados();
    if (!rados) {
        perror("init_rados");
        return EXIT_FAILURE;
    }

    sprintf(pool, "%s", argv[1]);
    rados_ioctx_t io_ctx = init_ioctx(rados, pool);
    if (!io_ctx) {
        perror("init_ioctx");
        rados_shutdown(rados);
        return EXIT_FAILURE;
    }

    sprintf(vol, "%s", argv[2]);
    rbd_image_t image = init_image(io_ctx, vol);
    if (!image) {
        perror("init_image");
        rados_ioctx_destroy(io_ctx);
        rados_shutdown(rados);
        return EXIT_FAILURE;
    }

    uint64_t size = get_rbd_size(image);
    //printf("image size: %lld\n", size);

    memset(buff, 1, 1024);  // 0~1023
    memset(buff + 1023, 0, 1024);  // 1024~2047
    memset(buff + 2047, 1, 1024);  // 2048~3071
    memset(buff + 3071, 0, 1024);  // 3072~4095
    len = 4096;

    time_t start = time(NULL);
    delay = atoi(argv[3]);
    while(!stop) {
        offset = (rand() * 1000ULL) % (size - len);
        aio_write(image, buff, len, offset);
        ++tx;
        //printf("write data len: %d, offset: %lld, count: %d\n", len, offset, tx);
        usleep(delay);
    }
    //aio_read(image, buff);

    time_t end = time(NULL);
    printf("elapse: %d, tx: %d\n", end - start, tx);

    while(rx != tx) {
        printf("tx: %d, rx: %d\n", tx, rx);
        sleep(1);
    }
    // 7. close image, io context and rados object
    ret = rbd_close(image);
    if (ret < 0) {
        printf("couldn't close rbd image! err %d\n", ret);
        return EXIT_FAILURE;
    } else {
        printf("closed rbd image: %s\n", vol);
    }
    rados_ioctx_destroy(io_ctx);
    rados_shutdown(rados);

    return 0;
}
