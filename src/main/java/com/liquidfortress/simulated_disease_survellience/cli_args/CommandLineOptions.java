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

import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.Option;
import org.apache.commons.cli.Options;

/**
 * CommandLineOptions
 * <p/>
 * Define and parse command line arguments
 */
public class CommandLineOptions {

    public static final String CLI_NAME = "lfsds";
    public static final String INPUT_CONFIG_FILE = "input-config-file";
    public static final String NODE_ID = "node-id";
    public static final String OUTPUT_FILE = "output-file";
    public static final String SILENT = "silent";
    public static final String VERBOSE = "verbose";
    public static final String HELP = "help";

    private static final Options options = new Options();
    private static final HelpFormatter helpFormatter = new HelpFormatter();
    private static final int width = 100;
    private static final String header = "";
    private static final String footer = "Example:  " + CLI_NAME + " -n 1 -f simulation.cfg";

    static {
        Option inputFile = Option.builder("f")
                .longOpt(INPUT_CONFIG_FILE)
                .hasArg()
                .argName("INPUT_CONFIG_FILE")
                .desc("Input configuration file in  format")
                .type(String.class)
                .required(true)
                .build();
        options.addOption(inputFile);

        Option nodeId = Option.builder("n")
                .longOpt(NODE_ID)
                .hasArg()
                .argName("NODE_ID")
                .desc("The node ID that this LFSDS instance should run from the input config file")
                .type(Integer.class)
                .required(true)
                .build();
        options.addOption(nodeId);

        Option outputFile = Option.builder("o")
                .longOpt(OUTPUT_FILE)
                .hasArg()
                .argName("OUTPUT_FILE")
                .type(String.class)
                .desc("Write output to the specified output file")
                .build();
        options.addOption(outputFile);

        Option silent = Option.builder("s")
                .longOpt(SILENT)
                .desc("Do not print output to the console")
                .build();
        options.addOption(silent);

        Option verbose = Option.builder("v")
                .longOpt(VERBOSE)
                .desc("Generate verbose output")
                .build();
        options.addOption(verbose);

        Option help = Option.builder("h")
                .longOpt(HELP)
                .desc("Print help and usage instructions")
                .build();
        options.addOption(help);
    }

    public static Options getCommandLineOptions() {
        return options;
    }

    public static void printHelp() {
        System.out.println("Liquid Fortress Simulated Disease Survellience");
        helpFormatter.printHelp(width, CLI_NAME, header, options, footer);
    }
}
