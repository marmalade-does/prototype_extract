#include <stdio.h>   // Required for file input/output operations (fopen, fclose, fgets, printf, fprintf)
#include <string.h>  // Required for string manipulation functions (strlen, strchr, strstr, strdup)
#include <stdlib.h>  // Required for general utilities (malloc, free, exit, strdup)
#include <ctype.h>   // Required for character classification functions (isspace)

// Define a maximum line length to prevent buffer overflows when reading lines
#define MAX_LINE_LENGTH 1024

/**
 * @brief Trims leading and trailing whitespace characters from a string in-place.
 *
 * This function modifies the input string by removing any whitespace characters
 * (spaces, tabs, newlines, etc.) from its beginning and end.
 *
 * @param str A pointer to the null-terminated string to be trimmed.
 */
void trim_whitespace(char *str) {
    char *end;

    // Trim leading space: Advance 'str' pointer past any leading whitespace.
    while (isspace((unsigned char)*str)) {
        str++;
    }

    // If the string consists entirely of spaces (or was empty), return early.
    if (*str == 0) {
        return;
    }

    // Trim trailing space: Find the end of the non-whitespace part.
    end = str + strlen(str) - 1;
    while (end > str && isspace((unsigned char)*end)) {
        end--;
    }

    // Place a new null terminator after the last non-whitespace character.
    *(end + 1) = 0;
}

/**
 * @brief Checks if a given string contains only whitespace characters.
 *
 * @param str A pointer to the null-terminated string to check.
 * @return 1 if the string contains only whitespace characters, 0 otherwise.
 */
int is_only_whitespace(const char *str) {
    while (*str) {
        if (!isspace((unsigned char)*str)) {
            return 0; // Found a non-whitespace character
        }
        str++;
    }
    return 1; // All characters were whitespace
}

/**
 * @brief Processes a single C source file to extract function prototypes.
 *
 * This function reads the file line by line, applies heuristics to identify
 * function definitions, and prints their corresponding prototypes to standard output.
 *
 * @param filename The path to the C source file to process.
 */
void process_file(const char *filename) {
    FILE *file = fopen(filename, "r");
    if (file == NULL) {
        // Print an error message if the file cannot be opened
        fprintf(stderr, "Error: Could not open file '%s'\n", filename);
        return;
    }

    char line[MAX_LINE_LENGTH]; // Buffer to store each line read from the file
    int in_multiline_comment = 0; // State variable to track if we are inside a multi-line comment

    // Read the file line by line until End-Of-File or an error occurs
    while (fgets(line, sizeof(line), file) != NULL) {
        // Create a mutable copy of the line because trim_whitespace modifies in-place
        // and we might need to null-terminate it for printing.
        char *current_line_copy = strdup(line);
        if (current_line_copy == NULL) {
            fprintf(stderr, "Memory allocation failed while processing file '%s'.\n", filename);
            break; // Exit the loop if memory allocation fails
        }

        // Trim leading and trailing whitespace from the copied line
        trim_whitespace(current_line_copy);

        // Skip empty lines after trimming
        if (strlen(current_line_copy) == 0) {
            free(current_line_copy); // Free the duplicated string
            continue;
        }

        // --- Basic Comment and Preprocessor Directive Handling ---
        // This is a heuristic and may not cover all complex cases.

        // If a line starts a multi-line comment (e.g., "/* comment") and doesn't end it on the same line,
        // set the 'in_multiline_comment' state to true.
        if (strstr(current_line_copy, "/*") != NULL && strstr(current_line_copy, "*/") == NULL) {
            in_multiline_comment = 1;
        }

        // If we are currently inside a multi-line comment block, skip the line.
        if (in_multiline_comment) {
            // If this line also contains the end of a multi-line comment (e.g., "*/"),
            // reset the 'in_multiline_comment' state.
            if (strstr(current_line_copy, "*/") != NULL) {
                in_multiline_comment = 0;
            }
            free(current_line_copy); // Free the duplicated string
            continue; // Move to the next line
        }

        // Skip preprocessor directives (lines starting with '#')
        if (current_line_copy[0] == '#') {
            free(current_line_copy);
            continue;
        }

        // Skip single-line comments (lines starting with '//')
        if (strstr(current_line_copy, "//") == current_line_copy) {
            free(current_line_copy);
            continue;
        }

        // --- Core Logic for Identifying Function Definitions ---
        // A function definition typically has: return_type function_name(arguments) {
        // We look for '(', then ')', then '{' in that order.

        // Find the first occurrence of '(' in the line
        char *open_paren = strchr(current_line_copy, '(');
        if (open_paren != NULL) {
            // Find the first occurrence of ')' after the '('
            char *close_paren = strchr(open_paren, ')');
            if (close_paren != NULL) {
                // Find the first occurrence of '{' after the ')'
                char *open_brace = strchr(close_paren, '{');
                if (open_brace != NULL) {
                    // Check if the characters between ')' and '{' are only whitespace.
                    // This helps distinguish function definitions from other code blocks (like if/for/while statements).
                    char *between_parens_brace_start = close_paren + 1; // Start checking after ')'

                    // Temporarily null-terminate the string at the '{' position
                    // to use is_only_whitespace on the segment between ')' and '{'.
                    char temp_char = *open_brace; // Store the character that was at '{' position
                    *open_brace = '\0';           // Replace it with null terminator

                    int only_ws = is_only_whitespace(between_parens_brace_start);

                    *open_brace = temp_char; // Restore the character at '{' position

                    if (only_ws) {
                        // If only whitespace was found, it's likely a function definition.
                        // Null-terminate the string at the brace to get just the prototype part.
                        *open_brace = '\0';
                        printf("%s;\n", current_line_copy); // Print the extracted prototype with a semicolon
                    }
                }
            }
        }
        free(current_line_copy); // Free the duplicated line after processing
    }

    fclose(file); // Close the file
}

/**
 * @brief Main function of the program.
 *
 * Handles command-line arguments (C source file names) and calls process_file
 * for each provided file.
 *
 * @param argc The number of command-line arguments.
 * @param argv An array of strings containing the command-line arguments.
 * argv[0] is the program name, argv[1...] are the filenames.
 * @return 0 on successful execution, 1 if insufficient arguments are provided.
 */
int main(int argc, char *argv[]) {
    // Check if at least one filename argument is provided
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <file1.c> [file2.c ...]\n", argv[0]);
        return 1; // Indicate an error by returning a non-zero value
    }

    // Iterate through each file provided as a command-line argument
    // (starting from argv[1] because argv[0] is the program's name)
    for (int i = 1; i < argc; i++) {
        process_file(argv[i]); // Call the function to process each file
    }

    return 0; // Indicate successful execution
}
