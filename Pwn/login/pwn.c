// gcc -pthread -O0 -o pwn pwn.c -lcrypto
#include <pthread.h>
#include <stddef.h>
#include <openssl/evp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_USERS 0x20
#define NAME_LEN 0x100
#define PASS_LEN 0x100
#define NOTE_LEN 0x400

typedef struct user{
    char username[NAME_LEN];
    char password[PASS_LEN];
    int is_admin;
}user_t;

typedef struct session{
    user_t* user;
    int logged_in;
    char note[NOTE_LEN];
}session_t;

typedef struct auth_cache{
    user_t* selected_user;
    char last_username[NAME_LEN];
    char verifier[PASS_LEN];
}auth_cache_t;

typedef struct login_arg{
    char username[NAME_LEN];
    char password[PASS_LEN];
}login_arg_t;

typedef struct register_arg{
    char username[NAME_LEN];
    char password[PASS_LEN];
}register_arg_t;

typedef struct note_arg{
    char note[NOTE_LEN];
}note_arg_t;

typedef struct switch_arg{
    char username[NAME_LEN];
}switch_arg_t;

static user_t* users[MAX_USERS];
static int user_count = 0;
static session_t* sessions[MAX_USERS];
static session_t* active_session = NULL;
static auth_cache_t auth_cache;

static pthread_mutex_t user_lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t session_lock = PTHREAD_MUTEX_INITIALIZER;

static void build_password_verifier(const char* username, const char* password, char* out, size_t size);

static void read_line(char* buf, size_t size)
{
    int c;
    size_t i = 0;
    if(size == 0) return;
    while(i < size - 1)
    {
        c = getchar();
        if(c == EOF)
        {
            puts("input error");
            exit(1);
        }
        if(c == '\n') break;
        buf[i++] = (char)c;
    }
    if(i == size-1) buf[i] = '\x00';
}

static void init_users(void)
{
    const char table[] = "abcdefghijklmnopqrstuvwxyz_+-*/@$#<>!?.ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    unsigned char buf[PASS_LEN] = {0};
    user_t* admin = NULL;
    FILE *fp = fopen("/dev/urandom", "rb");
    if(!fp)
    {
        perror("fopen");
        exit(1);
    }
    if (fread(buf, 1, sizeof(buf), fp) != sizeof(buf))
    {
        perror("fread");
        fclose(fp);
        exit(1);
    }
    fclose(fp);
    memset(users, 0, sizeof(users));
    memset(sessions, 0, sizeof(sessions));
    admin = (user_t*)calloc(1, sizeof(*admin));
    if(!admin)
    {
        puts("[!] calloc failed");
        exit(1);
    }
    users[0] = admin;
    snprintf(users[0]->username, sizeof(users[0]->username), "%s", "admin");
    for(size_t i = 0; i < sizeof(users[0]->password) - 1; i++)
    {
        users[0]->password[i] = table[buf[i] % (sizeof(table) - 1)];
    }
    users[0]->password[sizeof(users[0]->password) - 1] = '\x00';
    build_password_verifier(users[0]->username, users[0]->password, users[0]->password, sizeof(users[0]->password));
    users[0]->is_admin = 1;
    user_count = 1;
}

static user_t* find_user_locked(const char* username)
{
    for(int i = 0; i < MAX_USERS; i++)
    {
        if(users[i] && strcmp(users[i]->username, username) == 0)
            return users[i];
    }
    return NULL;
}

static int user_index_locked(user_t* user)
{
    if(!user) return -1;
    for(int i = 0; i < MAX_USERS; i++)
    {
        if(users[i] == user)
            return i;
    }
    return -1;
}

static session_t* session_for_user_locked(user_t* user)
{
    int index;
    if(!user) return NULL;
    index = user_index_locked(user);
    if(index < 0)  return NULL;
    return sessions[index];
}

static void build_password_verifier(const char* username, const char* password, char* out, size_t size)
{
    unsigned char digest[32];
    if(size < 65) return;
    if(PKCS5_PBKDF2_HMAC(password, (int)strlen(password), (const unsigned char*)username, (int)strlen(username), 50000, EVP_sha256(), sizeof(digest), digest) != 1)
    {
        out[0] = '\x00';
        return;
    }
    for(size_t i = 0; i < sizeof(digest); i++)
    {
        snprintf(out + i * 2, size - i * 2, "%02x", digest[i]);
    }
}

static void prepare_auth_cache_locked(user_t* user, const char* username)
{
    auth_cache.selected_user = user;
    snprintf(auth_cache.verifier, sizeof(auth_cache.verifier), "%s", user->password);
    snprintf(auth_cache.last_username, sizeof(auth_cache.last_username), "%s", username);
}

static int set_session_locked(user_t* user, const char* note)
{
    int index;
    session_t* session = session_for_user_locked(user);
    if(!session)
    {
        index = user_index_locked(user);
        if(index < 0) return -1;
        sessions[index] = (session_t*)calloc(1, sizeof(*sessions[index]));
        if(!sessions[index]) return -1;
        session = sessions[index];
    }
    memset(session, 0, sizeof(*session));
    session->user = user;
    session->logged_in = 1;
    snprintf(session->note, sizeof(session->note), "%s", note);
    active_session = session;
    return 0;
}

static void admin_menu(void)
{
    char buf[0x100];
    while (1)
    {
        int choice;
        memset(buf, 0, sizeof(buf));
        puts("");
        puts("1. edit user's username");
        puts("2. edit user's password");
        puts("3. change admin password");
        puts("4. logged out and return to login menu");
        printf("> ");
        read_line(buf, sizeof(buf));
        choice = atoi(buf);
        if(choice == 1)
        {
            memset(buf, 0, sizeof(buf));
            user_t* user = NULL;
            pthread_mutex_lock(&user_lock);
            printf("user index: ");
            read_line(buf, sizeof(buf));
            int idx = atoi(buf);
            if(idx >= MAX_USERS || !users[idx])
            {
                pthread_mutex_unlock(&user_lock);
                puts("[-] invalid user");
                continue;
            }
            user = users[idx];
            printf("new username: ");
            read_line(user->username, sizeof(user->username));
            pthread_mutex_unlock(&user_lock);
            puts("[+] edit done");
            continue;
        }else if(choice == 2){
            memset(buf, 0, sizeof(buf));
            user_t* user = NULL;
            pthread_mutex_lock(&user_lock);
            printf("user index: ");
            read_line(buf, sizeof(buf));
            int idx = atoi(buf);
            if(idx >= MAX_USERS || !users[idx])
            {
                pthread_mutex_unlock(&user_lock);
                puts("[-] invalid user");
                continue;
            }
            user = users[idx];
            printf("new password: ");
            read_line(buf, sizeof(buf));
            build_password_verifier(user->username, buf, user->password, sizeof(user->password));
            pthread_mutex_unlock(&user_lock);
            puts("[+] edit done");
            continue;
        }else if(choice == 3){
            memset(buf, 0, sizeof(buf));
            pthread_mutex_lock(&user_lock);
            printf("new admin password: ");
            read_line(buf, sizeof(buf));
            build_password_verifier(users[0]->username, buf, users[0]->password, sizeof(users[0]->password));
            pthread_mutex_unlock(&user_lock);
            puts("[+] changed admin password");
            continue;
        }else if(choice == 4){
            pthread_mutex_lock(&session_lock);
            if(active_session)
            {
                memset(active_session, 0, sizeof(*active_session));
                active_session = NULL;
            }
            pthread_mutex_unlock(&session_lock);
            puts("[+] logged out");
            return;
        }else{
            puts("[-] invalid choice");
        }
    }
}

static void user_menu(user_t* slot)
{
    char buf[0x100];
    while (1)
    {
        int choice;
        memset(buf, 0, sizeof(buf));
        puts("");
        puts("1. deregister");
        puts("2. change password");
        puts("3. logged out and return to login menu");
        printf("> ");
        read_line(buf, sizeof(buf));
        choice = atoi(buf);
        if(choice == 1)
        {
            int index;
            pthread_mutex_lock(&user_lock);
            pthread_mutex_lock(&session_lock);
            index = user_index_locked(slot);
            if(index >= 0 && sessions[index])
            {
                if(active_session == sessions[index])
                    active_session = NULL;
                free(sessions[index]);
                sessions[index] = NULL;
            }
            if(auth_cache.selected_user == slot)
            {
                auth_cache.selected_user = NULL;
                auth_cache.last_username[0] = '\x00';
                auth_cache.verifier[0] = '\x00';
            }
            if(active_session && active_session->user == slot)
                active_session = NULL;
            if(index >= 0)
                users[index] = NULL;
            free(slot);
            user_count--;
            pthread_mutex_unlock(&session_lock);
            pthread_mutex_unlock(&user_lock);
            puts("[+] deregistered");
            return;
        }else if(choice == 2){
            memset(buf, 0, sizeof(buf));
            pthread_mutex_lock(&user_lock);
            printf("new password: ");
            read_line(buf, sizeof(buf));
            build_password_verifier(slot->username, buf, slot->password, sizeof(slot->password));
            pthread_mutex_unlock(&user_lock);
            puts("[+] changed password");
            continue;
        }else if(choice == 3){
            pthread_mutex_lock(&session_lock);
            if(active_session)
            {
                memset(active_session, 0, sizeof(*active_session));
                active_session = NULL;
            }
            pthread_mutex_unlock(&session_lock);
            puts("[+] logged out");
            return;
        }else{
            puts("[-] invalid choice");
        }
    }
}

static void* register_worker(void* arg)
{
    register_arg_t* req = (register_arg_t*)arg;
    user_t* slot = NULL;
    pthread_mutex_lock(&user_lock);
    if(user_count >= MAX_USERS)
    {
        puts("[-] user table full");
        pthread_mutex_unlock(&user_lock);
        free(req);
        return NULL;
    }
    if(find_user_locked(req->username))
    {
        puts("[-] user already exists");
        pthread_mutex_unlock(&user_lock);
        free(req);
        return NULL;
    }
    for(int i = 0; i < MAX_USERS; i++)
    {
        if(!users[i])
        {
            users[i] = (user_t*)calloc(1, sizeof(*users[i]));
            if(!users[i])
            {
                puts("[-] calloc failed");
                pthread_mutex_unlock(&user_lock);
                free(req);
                return NULL;
            }
            slot = users[i];
            user_count++;
            break;
        }
    }
    if(!slot)
    {
        puts("[-] user table full");
        pthread_mutex_unlock(&user_lock);
        free(req);
        return NULL;
    }
    snprintf(slot->username, sizeof(slot->username), "%s", req->username);
    build_password_verifier(slot->username, req->password, slot->password, sizeof(slot->password));
    slot->is_admin = 0;
    pthread_mutex_unlock(&user_lock);
    printf("[+] registered: %s\n", slot->username);
    free(req);
    return NULL;
}

static void* login_worker(void* arg)
{
    login_arg_t* req = (login_arg_t*)arg;
    user_t* target = NULL;
    char session_note[NOTE_LEN];
    char supplied_verifier[PASS_LEN];
    pthread_mutex_lock(&user_lock);
    target = find_user_locked(req->username);
    if(!target)
    {
        pthread_mutex_unlock(&user_lock);
        puts("[-] no such user");
        free(req);
        return NULL;
    }
    prepare_auth_cache_locked(target, req->username);
    pthread_mutex_unlock(&user_lock);
    build_password_verifier(auth_cache.last_username, req->password, supplied_verifier, sizeof(supplied_verifier));
    if(target->is_admin)
    {
        snprintf(session_note, sizeof(session_note), "admin console ready");
    }else{
        snprintf(session_note, sizeof(session_note), "hello, %s", target->username);
    }
    pthread_mutex_lock(&user_lock);
    if(!auth_cache.selected_user)
    {
        pthread_mutex_unlock(&user_lock);
        puts("[-] invalid username or password");
        free(req);
        return NULL;
    }
    if(strcmp(supplied_verifier, auth_cache.verifier) != 0)
    {
        pthread_mutex_unlock(&user_lock);
        puts("[-] invalid username or password");
        free(req);
        return NULL;
    }
    pthread_mutex_unlock(&user_lock);
    pthread_mutex_lock(&session_lock);
    if(set_session_locked(target, session_note) != 0)
    {
        pthread_mutex_unlock(&session_lock);
        puts("[-] session setup failed");
        free(req);
        return NULL;
    }
    pthread_mutex_unlock(&session_lock);
    printf("[+] logged in as %s\n", target->username);
    free(req);
    return NULL;
}

static void* logout_worker(void* arg)
{
    (void)arg;
    pthread_mutex_lock(&session_lock);
    if(!active_session || !active_session->logged_in)
    {
        pthread_mutex_unlock(&session_lock);
        puts("[-] no active session");
        return NULL;
    }
    memset(active_session, 0, sizeof(*active_session));
    active_session = NULL;
    pthread_mutex_unlock(&session_lock);
    puts("[+] logged out");
    return NULL;
}

static void* whoami_worker(void* arg)
{
    session_t snapshot;
    (void)arg;
    pthread_mutex_lock(&session_lock);
    if (!active_session || !active_session->logged_in)
    {
        pthread_mutex_unlock(&session_lock);
        puts("[-] not logged in");
        return NULL;
    }
    snapshot = *active_session;
    pthread_mutex_unlock(&session_lock);
    printf("user: %s\n", snapshot.user->username);
    printf("role: %s\n", snapshot.user->is_admin ? "admin" : "user");
    printf("note: %s\n", snapshot.note);
    return NULL;
}

static void* edit_note_worker(void* arg)
{
    note_arg_t* req = (note_arg_t*)arg;
    pthread_mutex_lock(&session_lock);
    if(!active_session || !active_session->logged_in)
    {
        pthread_mutex_unlock(&session_lock);
        puts("[-] not logged in");
        free(req);
        return NULL;
    }
    snprintf(active_session->note, sizeof(active_session->note), "%s", req->note);
    pthread_mutex_unlock(&session_lock);
    puts("[+] note updated");
    free(req);
    return NULL;
}

static void* admin_worker(void* arg)
{
    int is_admin = 0;
    pthread_mutex_lock(&session_lock);
    if(!active_session || !active_session->logged_in)
    {
        pthread_mutex_unlock(&session_lock);
        puts("[-] login required");
        return NULL;
    }
    is_admin = active_session->user->is_admin;
    pthread_mutex_unlock(&session_lock);
    if(is_admin)
    {
        admin_menu();
    }else{
        puts("[-] admin only");
    }
    return NULL;
}

static void* user_worker(void* arg)
{
    user_t* slot = NULL;
    pthread_mutex_lock(&session_lock);
    if(!active_session || !active_session->logged_in)
    {
        pthread_mutex_unlock(&session_lock);
        puts("[-] login required");
        return NULL;
    }
    slot = active_session->user;
    pthread_mutex_unlock(&session_lock);
    user_menu(slot);
    return NULL;
}

static void* switch_worker(void* arg)
{
    switch_arg_t* req = (switch_arg_t*)arg;
    user_t* user = NULL;
    session_t* session = NULL;
    pthread_mutex_lock(&user_lock);
    user = find_user_locked(req->username);
    pthread_mutex_unlock(&user_lock);
    if(!user)
    {
        puts("[-] no such user");
        free(req);
        return NULL;
    }
    pthread_mutex_lock(&session_lock);
    session = session_for_user_locked(user);
    if(!session || !session->logged_in)
    {
        pthread_mutex_unlock(&session_lock);
        puts("[-] user is not logged in");
        free(req);
        return NULL;
    }
    active_session = session;
    pthread_mutex_unlock(&session_lock);
    printf("[+] switched to %s\n", user->username);
    free(req);
    return NULL;
}

static void launch_worker(void* (*fn)(void*), void* arg)
{
    pthread_t tid;
    if(pthread_create(&tid, NULL, fn, arg) != 0)
    {
        puts("[-] pthread_create failed");
        free(arg);
        return;
    }
    if(fn == admin_worker || fn == user_worker)
    {
        pthread_join(tid, NULL);
    }else{
        pthread_detach(tid);
    }
}

static void login_menu(void)
{
    puts("");
    puts("1. register");
    puts("2. login");
    puts("3. logout");
    puts("4. whoami");
    puts("5. edit session note");
    puts("6. admin menu");
    puts("7. user menu");
    puts("8. switch session");
    puts("9. exit");
    printf("> ");
}

int main(void)
{
    char buf[0x20] = {0};
    setbuf(stdin, NULL);
    setbuf(stdout, NULL);
    setbuf(stderr, NULL);
    init_users();
    puts("wow wow wow, you can do so many things");
    while (1)
    {
        int choice;
        memset(buf, 0, sizeof(buf));
        login_menu();
        read_line(buf, sizeof(buf));
        choice = atoi(buf);
        if(choice == 1)
        {
            register_arg_t* req = (register_arg_t*)calloc(1, sizeof(*req));
            if (!req)
            {
                puts("[-] calloc failed");
                continue;
            }
            printf("username: ");
            read_line(req->username, sizeof(req->username));
            printf("password: ");
            read_line(req->password, sizeof(req->password));
            launch_worker(register_worker, req);
        }else if(choice == 2){
            login_arg_t* req = (login_arg_t*)calloc(1, sizeof(*req));
            if (!req)
            {
                puts("[-] calloc failed");
                continue;
            }
            printf("username: ");
            read_line(req->username, sizeof(req->username));
            printf("password: ");
            read_line(req->password, sizeof(req->password));
            launch_worker(login_worker, req);
        }else if(choice == 3){
            launch_worker(logout_worker, NULL);
        }else if(choice == 4){
            launch_worker(whoami_worker, NULL);
        }else if(choice == 5){
            note_arg_t* req = (note_arg_t*)calloc(1, sizeof(*req));
            if(!req)
            {
                puts("[-] calloc failed");
                continue;
            }
            printf("note: ");
            read_line(req->note, sizeof(req->note));
            launch_worker(edit_note_worker, req);
        }else if(choice == 6){
            launch_worker(admin_worker, NULL);
        }else if(choice == 7){
            launch_worker(user_worker, NULL);
        }else if(choice == 8){
            switch_arg_t* req = (switch_arg_t*)calloc(1, sizeof(*req));
            if (!req)
            {
                puts("[-] calloc failed");
                continue;
            }
            printf("username: ");
            read_line(req->username, sizeof(req->username));
            launch_worker(switch_worker, req);
        }else if(choice == 9){
            break;
        }else{
            puts("[-] invalid choice");
        }
    }
    return 0;
}
