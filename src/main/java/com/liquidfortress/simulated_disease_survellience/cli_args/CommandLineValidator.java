/*
 * This file is part of Liquid Fortress Simulated Disease Survellience.
 * Copyright (c) 2018.  Richard Scott McNew.  All rights reserved.
 *
 * Developed by:  Richard Scott McNew
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy of this
 * software and associated documentation files (the "Software"), to deal with the
 * Software without restriction, including without limitation the rights to use, copy,
 * modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
 * to permit persons to whom the Software is furnished to do so, subject to the
 * following conditions:
 *
 * Redistributions of source code must retain the above copyright notice, this list of
 * conditions and the following disclaimers.
 *
 * Redistributions in binary form must reproduce the above copyright notice, this list of
 * conditions and the following disclaimers in the documentation and/or other materials
 * provided with the distribution.
 *
 * Neither the names of Richard Scott McNew, Liquid Fortress, nor the names of its
 * contributors may be used to endorse or promote products derived from this Software
 * without specific prior written permission.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
 * THE CONTRIBUTORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
 * DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
 * OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
 * THE USE OR OTHER DEALINGS WITH THE SOFTWARE.
 */

package com.liquidfortress.simulated_disease_survellience.cli_args;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.DefaultParser;
import org.apache.commons.cli.ParseException;

import java.io.File;

/**
 * CommandLineValidator
 * <p/>
 * Get and validate command line arguments
 */
public class CommandLineValidator {

    private static final CommandLineParser commandLineParser = new DefaultParser();

    // make sure the node ID is a positive number; a later comparison will make sure this node ID
    // is defined in the input configuration file
    private static boolean isNodeIdValid(CommandLine commandLine, ValidatedArgs validatedArgs) {
        if (commandLine.hasOption(CommandLineOptions.NODE_ID)) {
            try {
                validatedArgs.nodeId = Integer.valueOf(commandLine.getOptionValue(CommandLineOptions.NODE_ID));
                if (validatedArgs.nodeId > 0) {
                    return true;
                } else {
                    System.out.println("Provided Node ID must be a positive integer!");
                }
            } catch (NumberFormatException e) {
                System.out.println("Provided Node ID is not a positive integer!");
            }
        }
        return false;
    }

    // make sure the provided configuration file exists and is readable; the configuration file parser
    // will actually parse the file later to ensure it matches the required schema
    private static boolean isInputConfigurationFileValid(CommandLine commandLine, ValidatedArgs validatedArgs) {
        if (commandLine.hasOption(CommandLineOptions.INPUT_CONFIG_FILE)) {
            String inputConfigFileStr = commandLine.getOptionValue(CommandLineOptions.INPUT_CONFIG_FILE);
            validatedArgs.inputConfigFile = new File(inputConfigFileStr);
            // TODO: if no path separator is in inputConfigFileStr, assume current directory as path and append it
            if ((validatedArgs.inputConfigFile.exists()) && (validatedArgs.inputConfigFile.canRead())) {
                return true;
            } else {
                System.out.println("Input config file: " + inputConfigFileStr + " does not exist or cannot be read!");
            }
        }
        return false;
    }

    private static boolean isOutputFileValid(CommandLine commandLine, ValidatedArgs validatedArgs) {
        String outputFileStr = commandLine.getOptionValue(CommandLineOptions.OUTPUT_FILE);
        // TODO: if no path separator is in the outputFile String, assume current directory as path and append it
        // TODO: make sure the outputFile is not in the input file list
        validatedArgs.outputFile = new File(outputFileStr);
        boolean existsAndWritable = validatedArgs.outputFile.exists() && validatedArgs.outputFile.canWrite();
        boolean doesNotExistButWritablePath = (validatedArgs.outputFile.getParentFile() != null) &&
                (validatedArgs.outputFile.getParentFile().canWrite());
        return (existsAndWritable || doesNotExistButWritablePath);
    }

    public static ValidatedArgs validateCommandLineArgs(String[] args) {
        ValidatedArgs validatedArgs = new ValidatedArgs();
        CommandLine commandLine = null;
        try {
            commandLine = commandLineParser.parse(CommandLineOptions.getCommandLineOptions(), args);
            // help
            if (commandLine.hasOption(CommandLineOptions.HELP)) {
                CommandLineOptions.printHelp();
                System.exit(0);
            }
            // node id
            if (!isNodeIdValid(commandLine, validatedArgs)) {
                CommandLineOptions.printHelp();
                System.exit(-1);
            }
            // input configuration file
            if (!isInputConfigurationFileValid(commandLine, validatedArgs)) {
                CommandLineOptions.printHelp();
                System.exit(-2);
            }
            // output file
            if (commandLine.hasOption(CommandLineOptions.OUTPUT_FILE) && !isOutputFileValid(commandLine, validatedArgs)) {
                CommandLineOptions.printHelp();
                System.exit(-3);
            }
            // silent
            if (commandLine.hasOption(CommandLineOptions.SILENT)) {
                validatedArgs.silent = true;
                if (validatedArgs.outputFile == null) {
                    System.out.println("Silent and no output file means no output will occur.  You must specify an output file with silent!");
                    CommandLineOptions.printHelp();
                    System.exit(-4);
                }
            }
            // verbose
            if (commandLine.hasOption(CommandLineOptions.VERBOSE)) {
                validatedArgs.verbose = true;
            }
        } catch (ParseException e) {
            CommandLineOptions.printHelp();
            System.out.println("The error is:  " + e);
            System.exit(-9);
        }
        return validatedArgs;
    }
}
