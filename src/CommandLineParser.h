#ifndef COMMAND_LINE_PARSER_H
#define COMMAND_LINE_PARSER_H

#include <string>
#include <vector>
#include "McRogueFaceConfig.h"

class CommandLineParser {
public:
    struct ParseResult {
        bool should_exit = false;
        int exit_code = 0;
    };
    
    CommandLineParser(int argc, char* argv[]);
    ParseResult parse(McRogueFaceConfig& config);
    
private:
    int argc;
    char** argv;
    int current_arg = 1;  // Skip program name
    
    bool has_flag(const std::string& short_flag, const std::string& long_flag = "");
    std::string get_next_arg(const std::string& flag_name);
    void parse_positional_args(McRogueFaceConfig& config);
    void print_help();
    void print_version();
};

#endif // COMMAND_LINE_PARSER_H