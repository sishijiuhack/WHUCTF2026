#include <iostream>
#include <vector>
#include <stack>
#include <cstdint>
#include <memory>
#include <functional>

void init() 
{
    // scmp_filter_ctx ctx = seccomp_init(SCMP_ACT_ALLOW);
    // seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EACCES), SCMP_SYS(execve), 0);
    // seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EACCES), SCMP_SYS(execveat), 0);
    // seccomp_load(ctx);

    setbuf(stderr, NULL);
    setbuf(stdout, NULL);
    setbuf(stdin, NULL);
}

class VM{
private:
    // some basic containers for the vm
    std::vector<uint8_t> vm_code;
    size_t ip = 0;
    std::vector<size_t> vm_regs;
    std::vector<size_t> vm_data2;
    std::stack<size_t> vm_stack2;

    int exit_code;
    char exit_code_buffer[0x10];

    std::function<void()> stack_func;
    std::function<void()> data_func;
    std::function<void()> regs_func;
    std::function<void()> syscall_func;
    std::function<void()> exit_func;

    size_t vm_data[0x100];
    size_t vm_stack[0x100];
    int sp;

    bool leave_flag;
    static bool syscall_access;
    static bool func_updated;
    // some functions
    uint8_t getCode()
    {
        if(ip < vm_code.size())
        {
            return vm_code[ip++];
        }else{
            std::cout << "code index wrong!" << std::endl;
            return '\x00'; 
        }
    }
    void vm_reset()
    {
        while(!vm_stack2.empty()) vm_stack2.pop();
        vm_data2.assign(0x100, 0);
        vm_regs.assign(4, 0);
        if(!vm_code.empty()) vm_code.clear();
        ip = 0;
        sp = -1;

        stack_func = [this]() { this->vm_stack_op(); };
        data_func = [this]() { this->vm_data_op(); };
        regs_func = [this]() { this->vm_regs_op(); };
        syscall_func = [this]() { this->vm_syscall(); };
        exit_func = [this]() { this->vm_exit(); };

        leave_flag = false;
        exit_code = 0;
    }

    void vm_stack_op()
    {
        uint8_t optype = getCode();
        uint8_t reg_idx = getCode();
        if(reg_idx > 3)
        {
            std::cout << "reg index wrong!" << std::endl;
            exit(exit_code);
        }
        if(optype == '\x10') // push imm
        {
            size_t val = 0;
            for(int i =0; i < 8; i++)
            {
                val = (val << 8) | (uint8_t)getCode();
            }
            if(sp < 0xff)
            {
                vm_stack[++sp] = val;
            }else{
                std::cout << "you cant push when the stack is full" << std::endl;
                exit(exit_code);
            }
        }else if(optype == '\x11'){ // pop to reg
            
            if(sp < 0)
            {
                std::cout << "you cant pop when the stack is empty" << std::endl;
                exit(exit_code);
            }
            vm_regs[reg_idx] = vm_stack[sp];
            sp--;  
        }else if(optype == '\x12'){ // push reg
            size_t val = vm_regs[reg_idx];
            if(sp < 0xff)
            {
                vm_stack[++sp] = val;
            }else{
                std::cout << "you cant push when the stack is full" << std::endl;
                exit(exit_code);
            }
        }else{
            std::cout << "optype wrong!" << std::endl;
            exit(exit_code);
        } 
    }
    void vm_stack_op2()
    {
        uint8_t optype = getCode();
        uint8_t reg_idx = getCode();
        if(reg_idx > 3)
        {
            std::cout << "reg index wrong!" << std::endl;
            exit(exit_code);
        }
        if(optype == '\x10') // push
        {
            size_t val = 0;
            for(int i =0; i < 8; i++)
            {
                val = (val << 8) | getCode();
            }
            vm_stack2.push(val);
        }else if(optype == '\x11'){ // pop to reg
            if(vm_stack2.empty())
            {
                std::cout << "you cant pop when the stack is empty" << std::endl;
                exit(exit_code);
            }
            vm_regs[reg_idx] = vm_stack2.top();
            vm_stack2.pop();  
        }else if(optype == '\x12'){ // push reg
            size_t val = vm_regs[reg_idx];
            vm_stack2.push(val);
        }else{
            std::cout << "optype wrong!" << std::endl;
            exit(exit_code);
        } 
    }

    
    void vm_data_op()
    {
        char optype = getCode();
        char data_idx = getCode();
        char reg_idx = getCode();
        if(data_idx > 0xff)
        {
            std::cout << "data index wrong!" << std::endl;
            exit(exit_code);
        }
        if(reg_idx > 3)
        {
            std::cout << "reg index wrong!" << std::endl;
            exit(exit_code);
        }
        if(optype == '\x20')
        {                      // store from regs
            vm_data[data_idx] = vm_regs[reg_idx];
        }else if(optype == '\x21'){ // load to regs
            vm_regs[reg_idx] = vm_data[data_idx];
        }else{
            std::cout << "optype wrong!" << std::endl;
            exit(exit_code);
        }
    }
    void vm_data_op2()
    {
        uint8_t optype = getCode();
        uint8_t data_idx = getCode();
        uint8_t reg_idx = getCode();
        if(data_idx > 0xff)
        {
            std::cout << "data index wrong!" << std::endl;
            exit(exit_code);
        }
        if(reg_idx > 3)
        {
            std::cout << "reg index wrong!" << std::endl;
            exit(exit_code);
        }
        if(optype == '\x20')
        {                      // store from regs
            vm_data2[data_idx] = vm_regs[reg_idx];
        }else if(optype == '\x21'){ // load to regs
            vm_regs[reg_idx] = vm_data2[data_idx];
        }else{
            std::cout << "optype wrong!" << std::endl;
            exit(exit_code);
        }
    }


    void vm_regs_op()
    {
        uint8_t optype = getCode();
        uint8_t regs_idx[3];
        for(auto& reg_idx : regs_idx)
        {
            reg_idx = getCode();
            if(reg_idx > 3)
            {
                std::cout << "reg index wrong!" << std::endl;
                exit(exit_code);
            }
        }
        if(optype == '\x30') 
        {                      
            vm_regs[regs_idx[0]] = vm_regs[regs_idx[1]] + vm_regs[regs_idx[2]];
        }else if(optype == '\x31'){ 
            vm_regs[regs_idx[0]] = vm_regs[regs_idx[1]] - vm_regs[regs_idx[2]];
        }else if(optype == '\x32'){ 
            vm_regs[regs_idx[0]] = vm_regs[regs_idx[1]] * vm_regs[regs_idx[2]];
        }else if(optype == '\x33'){ 
            vm_regs[regs_idx[0]] = vm_regs[regs_idx[1]] / vm_regs[regs_idx[2]];
        }else if(optype == '\x34'){
            vm_regs[regs_idx[0]] = vm_regs[regs_idx[1]] & vm_regs[regs_idx[2]];
        }else if(optype == '\x35'){
            vm_regs[regs_idx[0]] = vm_regs[regs_idx[1]] | vm_regs[regs_idx[2]];
        }else if(optype == '\x36'){
            vm_regs[regs_idx[0]] = vm_regs[regs_idx[1]] ^ vm_regs[regs_idx[2]];
        }else if(optype == '\x37'){
            vm_regs[regs_idx[0]] = ~vm_regs[regs_idx[1]];
        }else if(optype == '\x38'){
            vm_regs[regs_idx[0]] = vm_regs[regs_idx[1]];
        }else if(optype == '\x39'){
            vm_regs[regs_idx[0]] = vm_regs[regs_idx[1]] << vm_regs[regs_idx[2]];
        }else if(optype == '\x40'){
            vm_regs[regs_idx[0]] = vm_regs[regs_idx[1]] >> vm_regs[regs_idx[2]];
        }else{
            std::cout << "optype wrong!" << std::endl;
            exit(exit_code);
        }
    }
    void vm_regs_op2()
    {
        uint8_t optype = getCode();
        uint8_t regs_idx[3];
        for(auto& reg_idx : regs_idx)
        {
            reg_idx = getCode();
            if(reg_idx > 3)
            {
                std::cout << "reg index wrong!" << std::endl;
                exit(exit_code);
            }
        }
        if(optype == '\x30') 
        {                      
            vm_regs[regs_idx[0]] = vm_regs[regs_idx[1]] + vm_regs[regs_idx[2]];
        }else if(optype == '\x31'){ 
            vm_regs[regs_idx[0]] = vm_regs[regs_idx[1]] - vm_regs[regs_idx[2]];
        }else if(optype == '\x32'){ 
            vm_regs[regs_idx[0]] = vm_regs[regs_idx[1]] * vm_regs[regs_idx[2]];
        }else if(optype == '\x34'){
            vm_regs[regs_idx[0]] = vm_regs[regs_idx[1]] & vm_regs[regs_idx[2]];
        }else if(optype == '\x35'){
            vm_regs[regs_idx[0]] = vm_regs[regs_idx[1]] | vm_regs[regs_idx[2]];
        }else if(optype == '\x36'){
            vm_regs[regs_idx[0]] = vm_regs[regs_idx[1]] ^ vm_regs[regs_idx[2]];
        }else if(optype == '\x37'){
            vm_regs[regs_idx[0]] = ~vm_regs[regs_idx[1]];
        }else if(optype == '\x38'){
            vm_regs[regs_idx[0]] = vm_regs[regs_idx[1]];
        }else if(optype == '\x39'){
            vm_regs[regs_idx[0]] = vm_regs[regs_idx[1]] << vm_regs[regs_idx[2]];
        }else if(optype == '\x40'){
            vm_regs[regs_idx[0]] = vm_regs[regs_idx[1]] >> vm_regs[regs_idx[2]];
        }else{
            std::cout << "optype wrong!" << std::endl;
            exit(exit_code);
        }
    }


    static size_t syscall_helper(size_t sysnum, size_t arg1, size_t arg2, size_t arg3)
    {
        size_t ret;
        asm volatile(
        "syscall"
        : "=a"(ret)                // rax 输出
        : "a"(sysnum),                 // rax = syscall number
          "D"(arg1),                  // rdi
          "S"(arg2),                  // rsi
          "d"(arg3)                   // rdx
        : "rcx", "r11", "memory"   // syscall 会破坏的寄存器
        );
        return ret;
    }
    void vm_syscall()
    {
        if(syscall_access)
        {
            syscall_helper(vm_regs[0], vm_regs[1], vm_regs[2], vm_regs[3]);
            syscall_access = false;
        }else{
            std::cout << "No syscall access!" << std::endl;
        }
        leave_flag = true;
    }
    void vm_syscall2()
    {
        std::cout << "No syscall access!" << std::endl;
        leave_flag = true;
    }

    void vm_exit()
    {
        exit(exit_code);
    }

    void vm_exit2()
    {
        std::cout << "set your exit code" << std::endl;
        std::cin >> exit_code_buffer;
        try{
            exit_code = std::stoi(std::string(exit_code_buffer));
        }catch(const std::exception& e){
            std::cout << "exit code error" << std::endl;
            exit_code = 0;
        }
        leave_flag = true;
    }

    void vm_operator()
    {
        char op;
        while((op = getCode()) != '\x00')
        {
            switch (op)
            {
            case 5: 
                exit_func();
                break;
            case 1: 
                stack_func();
                break;
            case 2: 
                data_func();
                break;
            case 3: 
                regs_func();
                break;
            case 4: 
                syscall_func();
                break;
            default:
                break;
            }

            if(leave_flag)
            {
                if(exit_code == -1) exit(exit_code);
                else exit_func();
            }
        }
        std::cout << "bye" << std::endl;
        exit(exit_code);
    }
public:
    VM()
    {
        vm_reset();
    }
    void updateFunc()
    {
        if(!func_updated)
        {
            stack_func = [this]() { this->vm_stack_op2(); };
            data_func = [this]() { this->vm_data_op2(); };
            regs_func = [this]() { this->vm_regs_op2(); };
            syscall_func = [this]() { this->vm_syscall2(); };
            exit_func = [this]() { this->vm_exit2(); };
            func_updated = true;
        }
    }
    void inputCode()
    {
        char ch;
        while(std::cin.get(ch) && ch != '\n')
        {
            vm_code.emplace_back(ch);
        }
    }
    void executeCode()
    {
        vm_operator();
    }
};

bool VM::func_updated = false;
bool VM::syscall_access = true;

int main()
{
    init();
    std::unique_ptr<VM> vm = std::make_unique<VM>();
    vm->updateFunc();
    std::cout << "input your code: " << std::endl;
    vm->inputCode();
    std::cout << "ok let's try it." << std::endl;
    vm->executeCode();
    return 0;
}
// g++ -no-pie vm.cpp -o pwn -g -z now