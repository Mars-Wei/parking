/*
 * Copyright (c) 2020, NVIDIA CORPORATION. All rights reserved.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
 * THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS IN THE SOFTWARE.
 */

#include <string>
#include <string.h>
#include <stdio.h>
#include <iostream>
#include <vector>
#include <assert.h>
#include <locale>
#include <codecvt>
#include "nvdsinfer.h"
#include <fstream>
#include <algorithm>

using namespace std;
using std::string;
using std::vector;

static bool dict_ready=false;
std::vector<string> dict_table;

extern "C"
{

bool NvDsInferParseCustomNVPlateTong(std::vector<NvDsInferLayerInfo> const &outputLayersInfo,
                                 NvDsInferNetworkInfo const &networkInfo, float classifierThreshold,
                                 std::vector<NvDsInferAttribute> &attrList, std::string &attrString)
{   
    // int *outputStrBuffer = NULL;
    // float *outputConfBuffer = NULL;
    // NvDsInferAttribute LPR_attr;
   
    // int seq_len = 0; 

    // Get list
    // vector<int> str_idxes;
    // int prev = 100;

    // For confidence
    // double bank_softmax_max[16] = {0.0};
    // unsigned int valid_bank_count = 0;
    // bool do_softmax = false;
    ifstream fdict;

    setlocale(LC_CTYPE, "");

    if (outputLayersInfo.size() != 1) {
        std::cerr << "Error: Expected exactly one output layer, but got " << outputLayersInfo.size() << std::endl;
        return false;
    }

    const NvDsInferLayerInfo &outputLayer = outputLayersInfo[0];

    // 假设 outputLayer 的维度为 [numClasses x seqLength]
    int numClasses = outputLayer.inferDims.d[0];
    std::cout << "--->[DEBUG] numClasses=: "<< numClasses << std::endl;
    int seqLength = outputLayer.inferDims.d[1];
    std::cout << "--->[DEBUG] seqLength=: "<< seqLength << std::endl;

    if (outputLayer.buffer == nullptr) {
        std::cerr << "Error: Output layer buffer is null" << std::endl;
        return false;
    }
    const float *outputData = static_cast<const float *>(outputLayer.buffer);

    if(!dict_ready) {
        fdict.open("models/LP/LPR/Tong-labels.txt");
        if(!fdict.is_open())
        {
            cout << "open dictionary file failed." << endl;
	        return false;
        }
	    while(!fdict.eof()) {
	        string strLineAnsi;
	        if ( getline(fdict, strLineAnsi) ) {
	            dict_table.push_back(strLineAnsi);
	        }
        }
        dict_ready=true;
        fdict.close();
    }

    if (dict_table.size() != static_cast<size_t>(numClasses)) {
        std::cerr << "Error: Number of labels in file does not match number of classes in output." << std::endl;
        return false;
    }

    std::vector<int> prebLabels;

    for (int j = 0; j < seqLength; ++j) {
        std::vector<float> prebColumn(numClasses);
        for (int i = 0; i < numClasses; ++i) {
            prebColumn[i] = outputData[i * seqLength + j]; // 按列访问数据
        }
        int maxIndex = std::distance(prebColumn.begin(), std::max_element(prebColumn.begin(), prebColumn.end()));
        prebLabels.push_back(maxIndex);
    }
    std::cout << "--->[DEBUG] prebLabels=[ "<< std::endl;
    for (const auto& value : prebLabels) {
        std::cout << value << " "; // 打印每个值，用空格分隔
    }
    std::cout << "--->[DEBUG] prebLabels end ] " << std::endl;
    // 构建 attrList 和 attrString
    attrList.clear();
    attrString.clear();

    for (int labelIndex : prebLabels) {
        if (labelIndex >= 0 && labelIndex < numClasses) {
            NvDsInferAttribute attr;
            attr.attributeIndex = labelIndex;
            attr.attributeValue = labelIndex;
            attr.attributeConfidence = 1.0; // 假设置信度为 1.0，可根据需要调整
            attrList.push_back(attr);

            // 从标签表中获取对应的标签字符串
            attrString += dict_table[labelIndex] + " ";
        }
    }

    // // 去掉末尾多余的空格
    // if (!attrString.empty() && attrString.back() == ' ') {
    //     attrString.pop_back();
    // }



    // for (auto it = dict_table.begin(); it != dict_table.end(); ++it) {
        // std::cout << *it << std::endl;
    // }
    // int layer_size = outputLayersInfo.size();
    // std::cout << "--->[DEBUG] layer_size=: "<< layer_size << std::endl;

    // LPR_attr.attributeConfidence = 1.0;

    // seq_len = networkInfo.width/4;
    // std::cout << "--->[DEBUG] seq_len= "<< seq_len << std::endl;

    // std::cout << "--->[DEBUG] outputLayersInfo1.buffer= "<< outputLayersInfo[1].buffer << std::endl;

    // for (int i = 0; i < layer_size; ++i) {
    //     const NvDsInferLayerInfo& layer = outputLayersInfo[i];

    //     // 打印每层的名称和大小
    //     std::cout << "Layer " << i << ": " << layer.dataType << ", size: " 
    //               << layer.inferDims.numElements << std::endl;

        // 假设 layer.data 是 float* 类型的指针
        // float* layerData = static_cast<float*>(layer.buffer);

        // 遍历当前层数据
        // for (size_t j = 0; j < layer.inferDims.numElements; ++j) {
            // float value = layerData[j];
            // std::cout << "Value at index " << j << ": " << value << std::endl;

            // 示例：用 dict_table 执行一些自定义逻辑
            // if (!dict_table.empty() && static_cast<size_t>(value) < dict_table.size()) {
            //     std::cout << "Matched label: " << dict_table[static_cast<size_t>(value)] << std::endl;
            // }
        // }
    // }

    // for( int li=0; li<layer_size; li++) {
    //     if(!outputLayersInfo[li].isInput) {
    //         if (outputLayersInfo[li].dataType == 0) {
    //             if (!outputConfBuffer){
    //                 outputConfBuffer = static_cast<float *>(outputLayersInfo[li].buffer);
    //                 std::cout << "--->[DEBUG] outputConfBuffer= "<< outputConfBuffer << std::endl;
    //             }
    //         }else if (outputLayersInfo[li].dataType == 3) {
    //             if(!outputStrBuffer){
    //                 outputStrBuffer = static_cast<int *>(outputLayersInfo[li].buffer);
    //                 std::cout << "--->[DEBUG] outputStrBuffer= "<< outputStrBuffer << std::endl;
    //             }
    //         }
    //     }
    // }

    // for(int seq_id = 0; seq_id < seq_len; seq_id++) {
    //    do_softmax = false;

    //    int curr_data = outputStrBuffer[seq_id];
    //    std::cout << "--->[DEBUG] curr_data=: "<< curr_data << std::endl;
    //    if (seq_id == 0) {
    //        prev = curr_data;
    //        str_idxes.push_back(curr_data);
    //     //    if ( curr_data != static_cast<int>(dict_table.size()) ) do_softmax = true;
    //    } else {
    //        if (curr_data != prev) {
    //            str_idxes.push_back(curr_data);
    //         //    if (static_cast<unsigned long>(curr_data) != dict_table.size()) do_softmax = true;
    //        }
    //        prev = curr_data;
    //    }

       // Do softmax
    //    if (do_softmax) {
    //        do_softmax = false;
    //        bank_softmax_max[valid_bank_count] = outputConfBuffer[curr_data];
    //        valid_bank_count++;
    //    }
    // }

    // attrString = "";
    // for(unsigned int id = 0; id < str_idxes.size(); id++) {
    //     if (static_cast<unsigned int>(str_idxes[id]) != dict_table.size()) {
    //         attrString += dict_table[str_idxes[id]];
    //         std::cout << "--->[DEBUG] attrString=: "<< attrString << std::endl;
    //     }
    // }

    // //Ignore the short string, it may be wrong plate string
    // if (valid_bank_count >=  3) {

    //     LPR_attr.attributeIndex = 0;
    //     LPR_attr.attributeValue = 1;
    //     LPR_attr.attributeLabel = strdup(attrString.c_str());
    //     for (unsigned int count = 0; count < valid_bank_count; count++) {
    //         LPR_attr.attributeConfidence *= bank_softmax_max[count];
    //     }
    //     attrList.push_back(LPR_attr);
	// std::cout << "--->[DEBUG]: "<< LPR_attr.attributeLabel << std::endl;
    // }

    return true;
}

}//end of extern "C"
