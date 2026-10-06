#include "bounded_regex.h"
#include <algorithm>
#include <cstdint>
#include <cwctype>
#include <memory>
#include <utility>
#include <vector>

namespace fxfile::boundedregex {
namespace {

constexpr std::size_t kMaxPatternChars=256;
constexpr std::size_t kMaxAstDepth=32;
constexpr std::size_t kMaxRepeat=64;
constexpr std::size_t kMaxStates=1024;
constexpr std::uint64_t kMaxMatchSteps=8ull*1024ull*1024ull;

enum class AtomKind {
    Literal,
    Any,
    Digit,
    NotDigit,
    Word,
    NotWord,
    Space,
    NotSpace,
    Class,
};

struct CharRange final {
    wchar_t first=0;
    wchar_t last=0;
};

struct Atom final {
    AtomKind kind=AtomKind::Literal;
    wchar_t literal=0;
    bool negated=false;
    std::vector<CharRange> ranges;
};

enum class NodeKind {
    Atom,
    Concat,
    Alternate,
    Repeat,
    Begin,
    End,
};

struct Node final {
    NodeKind kind=NodeKind::Atom;
    Atom atom{};
    std::vector<std::unique_ptr<Node>> children;
    std::size_t minRepeat=1;
    std::size_t maxRepeat=1;
    bool unlimited=false;
};

int hexDigit(wchar_t ch) noexcept
{
    if(ch>=L'0'&&ch<=L'9')return static_cast<int>(ch-L'0');
    if(ch>=L'a'&&ch<=L'f')return 10+static_cast<int>(ch-L'a');
    if(ch>=L'A'&&ch<=L'F')return 10+static_cast<int>(ch-L'A');
    return -1;
}

class Parser final {
public:
    explicit Parser(std::wstring const& input):input_(input){}

    std::unique_ptr<Node> parse() {
        if(input_.empty()||input_.size()>kMaxPatternChars){
            result_=input_.empty()?CompileResult::InvalidSyntax:
                                   CompileResult::TooComplex;
            return {};
        }
        auto root=parseExpression(0);
        if(!root||result_!=CompileResult::Valid)return {};
        if(pos_!=input_.size()){
            result_=CompileResult::InvalidSyntax;
            return {};
        }
        return root;
    }

    CompileResult result() const noexcept { return result_; }

private:
    std::wstring const& input_;
    std::size_t pos_=0;
    CompileResult result_=CompileResult::Valid;

    void fail(CompileResult value) noexcept {
        if(result_==CompileResult::Valid)result_=value;
    }

    bool atEnd() const noexcept { return pos_>=input_.size(); }
    wchar_t peek() const noexcept { return atEnd()?0:input_[pos_]; }
    wchar_t take() noexcept { return atEnd()?0:input_[pos_++]; }

    std::unique_ptr<Node> makeAtom(Atom value) {
        auto node=std::make_unique<Node>();
        node->kind=NodeKind::Atom;
        node->atom=std::move(value);
        return node;
    }

    std::unique_ptr<Node> parseExpression(std::size_t depth) {
        if(depth>kMaxAstDepth){
            fail(CompileResult::TooComplex);
            return {};
        }
        auto first=parseConcat(depth);
        if(!first)return {};
        if(peek()!=L'|')return first;

        auto alt=std::make_unique<Node>();
        alt->kind=NodeKind::Alternate;
        alt->children.push_back(std::move(first));
        while(peek()==L'|'){
            take();
            auto next=parseConcat(depth);
            if(!next)return {};
            alt->children.push_back(std::move(next));
        }
        return alt;
    }

    std::unique_ptr<Node> parseConcat(std::size_t depth) {
        std::vector<std::unique_ptr<Node>> parts;
        while(!atEnd()&&peek()!=L')'&&peek()!=L'|'){
            auto part=parseRepeated(depth);
            if(!part)return {};
            parts.push_back(std::move(part));
        }
        if(parts.empty()){
            fail(CompileResult::InvalidSyntax);
            return {};
        }
        if(parts.size()==1)return std::move(parts.front());
        auto concat=std::make_unique<Node>();
        concat->kind=NodeKind::Concat;
        concat->children=std::move(parts);
        return concat;
    }

    bool parseNumber(std::size_t& value) {
        value=0;
        std::size_t digits=0;
        while(!atEnd()&&peek()>=L'0'&&peek()<=L'9'){
            const auto digit=static_cast<std::size_t>(take()-L'0');
            if(value>(kMaxRepeat-digit)/10){
                fail(CompileResult::TooComplex);
                return false;
            }
            value=value*10+digit;
            ++digits;
        }
        if(!digits){
            fail(CompileResult::InvalidSyntax);
            return false;
        }
        if(value>kMaxRepeat){
            fail(CompileResult::TooComplex);
            return false;
        }
        return true;
    }

    std::unique_ptr<Node> parseRepeated(std::size_t depth) {
        auto atom=parseAtom(depth);
        if(!atom)return {};

        const wchar_t ch=peek();
        if(ch!=L'*'&&ch!=L'+'&&ch!=L'?'&&ch!=L'{')
            return atom;
        if(atom->kind==NodeKind::Begin||atom->kind==NodeKind::End){
            fail(CompileResult::InvalidSyntax);
            return {};
        }

        std::size_t min=1,max=1;
        bool unlimited=false;
        if(ch==L'*'){
            take();min=0;unlimited=true;
        }else if(ch==L'+'){
            take();min=1;unlimited=true;
        }else if(ch==L'?'){
            take();min=0;max=1;
        }else{
            take();
            if(!parseNumber(min))return {};
            if(peek()==L'}'){
                take();max=min;
            }else if(peek()==L','){
                take();
                if(peek()==L'}'){
                    take();unlimited=true;
                }else{
                    if(!parseNumber(max))return {};
                    if(peek()!=L'}'){
                        fail(CompileResult::InvalidSyntax);
                        return {};
                    }
                    take();
                    if(min>max){
                        fail(CompileResult::InvalidSyntax);
                        return {};
                    }
                }
            }else{
                fail(CompileResult::InvalidSyntax);
                return {};
            }
        }

        if(peek()==L'?')take(); // lazy vs greedy does not affect boolean search.
        if(peek()==L'+'||peek()==L'*'||peek()==L'?'||peek()==L'{'){
            fail(CompileResult::InvalidSyntax);
            return {};
        }

        auto repeat=std::make_unique<Node>();
        repeat->kind=NodeKind::Repeat;
        repeat->minRepeat=min;
        repeat->maxRepeat=max;
        repeat->unlimited=unlimited;
        repeat->children.push_back(std::move(atom));
        return repeat;
    }

    bool parseHex(std::size_t digits,wchar_t& value) {
        unsigned code=0;
        for(std::size_t i=0;i<digits;++i){
            if(atEnd()){
                fail(CompileResult::InvalidSyntax);
                return false;
            }
            const int digit=hexDigit(take());
            if(digit<0){
                fail(CompileResult::InvalidSyntax);
                return false;
            }
            code=(code<<4)|static_cast<unsigned>(digit);
        }
        value=static_cast<wchar_t>(code);
        return true;
    }

    std::unique_ptr<Node> parseEscape() {
        if(atEnd()){
            fail(CompileResult::InvalidSyntax);
            return {};
        }
        const wchar_t ch=take();
        Atom atom{};
        switch(ch){
        case L'd': atom.kind=AtomKind::Digit;return makeAtom(std::move(atom));
        case L'D': atom.kind=AtomKind::NotDigit;return makeAtom(std::move(atom));
        case L'w': atom.kind=AtomKind::Word;return makeAtom(std::move(atom));
        case L'W': atom.kind=AtomKind::NotWord;return makeAtom(std::move(atom));
        case L's': atom.kind=AtomKind::Space;return makeAtom(std::move(atom));
        case L'S': atom.kind=AtomKind::NotSpace;return makeAtom(std::move(atom));
        case L'b':
        case L'B':
            fail(CompileResult::Unsupported);
            return {};
        case L'n': atom.literal=L'\n';break;
        case L'r': atom.literal=L'\r';break;
        case L't': atom.literal=L'\t';break;
        case L'f': atom.literal=L'\f';break;
        case L'v': atom.literal=L'\v';break;
        case L'x':
            if(!parseHex(2,atom.literal))return {};
            break;
        case L'u':
            if(!parseHex(4,atom.literal))return {};
            break;
        default:
            if(ch>=L'1'&&ch<=L'9'){
                fail(CompileResult::Unsupported);
                return {};
            }
            atom.literal=ch;
            break;
        }
        atom.kind=AtomKind::Literal;
        return makeAtom(std::move(atom));
    }

    bool appendClassEscape(Atom& atom) {
        if(atEnd()){
            fail(CompileResult::InvalidSyntax);
            return false;
        }
        const wchar_t ch=take();
        auto add=[&](wchar_t first,wchar_t last){
            atom.ranges.push_back(CharRange{first,last});
        };
        switch(ch){
        case L'd': add(L'0',L'9');return true;
        case L'w':
            add(L'0',L'9');add(L'A',L'Z');add(L'a',L'z');add(L'_',L'_');
            return true;
        case L's':
            add(L'\t',L'\t');add(L'\n',L'\n');add(L'\v',L'\v');
            add(L'\f',L'\f');add(L'\r',L'\r');add(L' ',L' ');
            return true;
        case L'D':
        case L'W':
        case L'S':
        case L'b':
        case L'B':
            fail(CompileResult::Unsupported);
            return false;
        default:{
            wchar_t value=ch;
            if(ch==L'n')value=L'\n';
            else if(ch==L'r')value=L'\r';
            else if(ch==L't')value=L'\t';
            else if(ch==L'f')value=L'\f';
            else if(ch==L'v')value=L'\v';
            else if(ch==L'x'){
                if(!parseHex(2,value))return false;
            }else if(ch==L'u'){
                if(!parseHex(4,value))return false;
            }
            add(value,value);
            return true;
        }}
    }

    bool parseClassLiteral(wchar_t& value) {
        if(atEnd()){
            fail(CompileResult::InvalidSyntax);
            return false;
        }
        if(peek()==L'\\'){
            take();
            if(atEnd()){
                fail(CompileResult::InvalidSyntax);
                return false;
            }
            const wchar_t ch=take();
            if(ch==L'x')return parseHex(2,value);
            if(ch==L'u')return parseHex(4,value);
            if(ch==L'n')value=L'\n';
            else if(ch==L'r')value=L'\r';
            else if(ch==L't')value=L'\t';
            else if(ch==L'f')value=L'\f';
            else if(ch==L'v')value=L'\v';
            else if(ch==L'd'||ch==L'w'||ch==L's'||
                    ch==L'D'||ch==L'W'||ch==L'S'){
                fail(CompileResult::Unsupported);
                return false;
            }else value=ch;
            return true;
        }
        value=take();
        return true;
    }

    std::unique_ptr<Node> parseClass() {
        take(); // [
        Atom atom{};
        atom.kind=AtomKind::Class;
        if(peek()==L'^'){
            take();
            atom.negated=true;
        }
        bool any=false;
        while(!atEnd()&&peek()!=L']'){
            if(peek()==L'\\'){
                const auto before=atom.ranges.size();
                take();
                if(!appendClassEscape(atom))return {};
                any=any||atom.ranges.size()>before;
                continue;
            }
            wchar_t first=0;
            if(!parseClassLiteral(first))return {};
            if(peek()==L'-'&&pos_+1<input_.size()&&input_[pos_+1]!=L']'){
                take();
                wchar_t last=0;
                if(!parseClassLiteral(last))return {};
                if(first>last){
                    fail(CompileResult::InvalidSyntax);
                    return {};
                }
                atom.ranges.push_back(CharRange{first,last});
            }else{
                atom.ranges.push_back(CharRange{first,first});
            }
            any=true;
        }
        if(atEnd()||peek()!=L']'||!any){
            fail(CompileResult::InvalidSyntax);
            return {};
        }
        take();
        return makeAtom(std::move(atom));
    }

    std::unique_ptr<Node> parseAtom(std::size_t depth) {
        if(atEnd()){
            fail(CompileResult::InvalidSyntax);
            return {};
        }
        const wchar_t ch=peek();
        if(ch==L'('){
            take();
            bool nonCapturing=false;
            if(peek()==L'?'){
                if(pos_+1<input_.size()&&input_[pos_+1]==L':'){
                    pos_+=2;
                    nonCapturing=true;
                }else{
                    fail(CompileResult::Unsupported);
                    return {};
                }
            }
            (void)nonCapturing;
            auto group=parseExpression(depth+1);
            if(!group)return {};
            if(peek()!=L')'){
                fail(CompileResult::InvalidSyntax);
                return {};
            }
            take();
            return group;
        }
        if(ch==L')'||ch==L'|'||ch==L'*'||ch==L'+'||ch==L'?'||ch==L'{'){
            fail(CompileResult::InvalidSyntax);
            return {};
        }
        if(ch==L'[')return parseClass();
        if(ch==L'\\'){
            take();
            return parseEscape();
        }
        if(ch==L'.'){
            take();
            Atom atom{};atom.kind=AtomKind::Any;
            return makeAtom(std::move(atom));
        }
        if(ch==L'^'){
            take();
            auto node=std::make_unique<Node>();
            node->kind=NodeKind::Begin;
            return node;
        }
        if(ch==L'$'){
            take();
            auto node=std::make_unique<Node>();
            node->kind=NodeKind::End;
            return node;
        }

        take();
        Atom atom{};
        atom.kind=AtomKind::Literal;
        atom.literal=ch;
        return makeAtom(std::move(atom));
    }
};

enum class StateKind {
    Epsilon,
    Atom,
    Split,
    Begin,
    End,
    Match,
};

struct State final {
    StateKind kind=StateKind::Epsilon;
    Atom atom{};
    int out1=-1;
    int out2=-1;
};

struct Patch final {
    int state=-1;
    bool second=false;
};

struct Fragment final {
    int start=-1;
    std::vector<Patch> outs;
};

class Compiler final {
public:
    CompileResult build(Node const& root,std::vector<State>& states,int& start) {
        states_.clear();
        result_=CompileResult::Valid;
        auto fragment=compile(root);
        if(result_!=CompileResult::Valid)return result_;
        const int match=emit(State{StateKind::Match,{},-1,-1});
        if(match<0)return result_;
        patch(fragment.outs,match);
        states=std::move(states_);
        start=fragment.start;
        return result_;
    }

private:
    std::vector<State> states_;
    CompileResult result_=CompileResult::Valid;

    int emit(State value) {
        if(states_.size()>=kMaxStates){
            result_=CompileResult::TooComplex;
            return -1;
        }
        states_.push_back(std::move(value));
        return static_cast<int>(states_.size()-1);
    }

    void patch(std::vector<Patch> const& outs,int target) {
        for(const auto& value:outs){
            if(value.state<0||static_cast<std::size_t>(value.state)>=states_.size()){
                result_=CompileResult::InvalidSyntax;
                return;
            }
            if(value.second)states_[value.state].out2=target;
            else states_[value.state].out1=target;
        }
    }

    Fragment epsilon() {
        const int state=emit(State{StateKind::Epsilon,{},-1,-1});
        if(state<0)return {};
        return Fragment{state,{{state,false}}};
    }

    Fragment concat(Fragment left,Fragment right) {
        if(result_!=CompileResult::Valid)return {};
        patch(left.outs,right.start);
        left.outs=std::move(right.outs);
        return left;
    }

    Fragment compileRepeat(Node const& node) {
        Fragment result=epsilon();
        for(std::size_t i=0;i<node.minRepeat;++i){
            auto body=compile(*node.children[0]);
            result=concat(std::move(result),std::move(body));
            if(result_!=CompileResult::Valid)return {};
        }

        if(node.unlimited){
            auto body=compile(*node.children[0]);
            if(result_!=CompileResult::Valid)return {};
            const int split=emit(State{StateKind::Split,{},body.start,-1});
            if(split<0)return {};
            patch(body.outs,split);
            Fragment tail{split,{{split,true}}};
            result=concat(std::move(result),std::move(tail));
        }else{
            for(std::size_t i=node.minRepeat;i<node.maxRepeat;++i){
                auto body=compile(*node.children[0]);
                if(result_!=CompileResult::Valid)return {};
                const int split=emit(State{StateKind::Split,{},body.start,-1});
                if(split<0)return {};
                auto outs=std::move(body.outs);
                outs.push_back(Patch{split,true});
                Fragment optional{split,std::move(outs)};
                result=concat(std::move(result),std::move(optional));
            }
        }
        return result;
    }

    Fragment compile(Node const& node) {
        if(result_!=CompileResult::Valid)return {};
        switch(node.kind){
        case NodeKind::Atom:{
            State state{};
            state.kind=StateKind::Atom;
            state.atom=node.atom;
            const int index=emit(std::move(state));
            return index<0?Fragment{}:Fragment{index,{{index,false}}};
        }
        case NodeKind::Begin:{
            const int index=emit(State{StateKind::Begin,{},-1,-1});
            return index<0?Fragment{}:Fragment{index,{{index,false}}};
        }
        case NodeKind::End:{
            const int index=emit(State{StateKind::End,{},-1,-1});
            return index<0?Fragment{}:Fragment{index,{{index,false}}};
        }
        case NodeKind::Concat:{
            auto result=compile(*node.children[0]);
            for(std::size_t i=1;i<node.children.size();++i)
                result=concat(std::move(result),compile(*node.children[i]));
            return result;
        }
        case NodeKind::Alternate:{
            auto result=compile(*node.children[0]);
            for(std::size_t i=1;i<node.children.size();++i){
                auto right=compile(*node.children[i]);
                if(result_!=CompileResult::Valid)return {};
                const int split=emit(
                    State{StateKind::Split,{},result.start,right.start});
                if(split<0)return {};
                result.outs.insert(
                    result.outs.end(),right.outs.begin(),right.outs.end());
                result.start=split;
            }
            return result;
        }
        case NodeKind::Repeat:
            return compileRepeat(node);
        default:
            result_=CompileResult::InvalidSyntax;
            return {};
        }
    }
};

wchar_t folded(wchar_t value) noexcept
{
    return static_cast<wchar_t>(std::towlower(value));
}

bool sameChar(wchar_t left,wchar_t right,bool caseSensitive) noexcept
{
    return caseSensitive?left==right:folded(left)==folded(right);
}

bool atomMatches(Atom const& atom,wchar_t ch,bool caseSensitive) noexcept
{
    switch(atom.kind){
    case AtomKind::Literal:
        return sameChar(atom.literal,ch,caseSensitive);
    case AtomKind::Any:
        return ch!=L'\r'&&ch!=L'\n';
    case AtomKind::Digit:
        return std::iswdigit(ch)!=0;
    case AtomKind::NotDigit:
        return std::iswdigit(ch)==0;
    case AtomKind::Word:
        return std::iswalnum(ch)!=0||ch==L'_';
    case AtomKind::NotWord:
        return std::iswalnum(ch)==0&&ch!=L'_';
    case AtomKind::Space:
        return std::iswspace(ch)!=0;
    case AtomKind::NotSpace:
        return std::iswspace(ch)==0;
    case AtomKind::Class:{
        const wchar_t value=caseSensitive?ch:folded(ch);
        bool hit=false;
        for(const auto& range:atom.ranges){
            const wchar_t first=caseSensitive?range.first:folded(range.first);
            const wchar_t last=caseSensitive?range.last:folded(range.last);
            const wchar_t low=(std::min)(first,last);
            const wchar_t high=(std::max)(first,last);
            if(value>=low&&value<=high){
                hit=true;
                break;
            }
        }
        return atom.negated?!hit:hit;
    }
    default:
        return false;
    }
}

bool containsMatch(std::vector<int> const& active,
                   std::vector<State> const& states) noexcept
{
    for(const int index:active)
        if(index>=0&&static_cast<std::size_t>(index)<states.size()&&
           states[index].kind==StateKind::Match)
            return true;
    return false;
}

} // namespace

struct Pattern::Impl final {
    std::vector<State> states;
    int start=-1;
    bool caseSensitive=false;

    MatchResult search(
        std::wstring const& text,
        std::shared_ptr<std::atomic_bool> const& cancel) const noexcept
    {
        try{
            if(start<0||states.empty())return MatchResult::NoMatch;

            std::vector<int> current,next,stack;
            current.reserve(states.size());
            next.reserve(states.size());
            stack.reserve(states.size());
            std::vector<std::uint32_t> seen(states.size(),0);
            std::uint32_t generation=1;
            std::uint64_t steps=0;
            bool canceled=false;
            bool budgetExceeded=false;

            auto nextGeneration=[&]() {
                ++generation;
                if(!generation){
                    std::fill(seen.begin(),seen.end(),0);
                    generation=1;
                }
            };

            auto addClosure=[&](
                int initial,std::size_t position,
                std::vector<int>& output) {
                stack.clear();
                if(initial>=0)stack.push_back(initial);
                while(!stack.empty()){
                    const int index=stack.back();
                    stack.pop_back();
                    if(index<0||static_cast<std::size_t>(index)>=states.size())
                        continue;
                    if(seen[index]==generation)continue;
                    seen[index]=generation;

                    if(++steps>kMaxMatchSteps){
                        budgetExceeded=true;
                        return;
                    }
                    if((steps&0xfffull)==0&&cancel&&cancel->load()){
                        canceled=true;
                        return;
                    }

                    const auto& state=states[index];
                    switch(state.kind){
                    case StateKind::Epsilon:
                        stack.push_back(state.out1);
                        break;
                    case StateKind::Split:
                        stack.push_back(state.out1);
                        stack.push_back(state.out2);
                        break;
                    case StateKind::Begin:
                        if(position==0)stack.push_back(state.out1);
                        break;
                    case StateKind::End:
                        if(position==text.size())stack.push_back(state.out1);
                        break;
                    case StateKind::Atom:
                    case StateKind::Match:
                        output.push_back(index);
                        break;
                    default:
                        break;
                    }
                }
            };

            addClosure(start,0,current);
            if(canceled)return MatchResult::Canceled;
            if(budgetExceeded)return MatchResult::BudgetExceeded;
            if(containsMatch(current,states))return MatchResult::Match;

            for(std::size_t position=0;position<text.size();++position){
                if(cancel&&cancel->load())return MatchResult::Canceled;
                next.clear();
                nextGeneration();

                for(const int index:current){
                    if(index<0||static_cast<std::size_t>(index)>=states.size())
                        continue;
                    const auto& state=states[index];
                    if(state.kind!=StateKind::Atom)continue;
                    if(++steps>kMaxMatchSteps)
                        return MatchResult::BudgetExceeded;
                    if(atomMatches(state.atom,text[position],caseSensitive)){
                        addClosure(state.out1,position+1,next);
                        if(canceled)return MatchResult::Canceled;
                        if(budgetExceeded)return MatchResult::BudgetExceeded;
                    }
                }

                addClosure(start,position+1,next);
                if(canceled)return MatchResult::Canceled;
                if(budgetExceeded)return MatchResult::BudgetExceeded;
                current.swap(next);
                if(containsMatch(current,states))return MatchResult::Match;
            }
            return MatchResult::NoMatch;
        }catch(...){
            return MatchResult::BudgetExceeded;
        }
    }
};

Pattern::Pattern()=default;
Pattern::Pattern(Pattern&&) noexcept=default;
Pattern& Pattern::operator=(Pattern&&) noexcept=default;
Pattern::~Pattern()=default;

CompileResult Pattern::compile(
    std::wstring const& pattern,bool caseSensitive) noexcept
{
    try{
        Parser parser(pattern);
        auto root=parser.parse();
        if(!root){
            impl_.reset();
            return parser.result();
        }

        std::vector<State> states;
        int start=-1;
        Compiler compiler;
        const auto result=compiler.build(*root,states,start);
        if(result!=CompileResult::Valid){
            impl_.reset();
            return result;
        }

        auto next=std::make_unique<Impl>();
        next->states=std::move(states);
        next->start=start;
        next->caseSensitive=caseSensitive;
        impl_=std::move(next);
        return CompileResult::Valid;
    }catch(...){
        impl_.reset();
        return CompileResult::TooComplex;
    }
}

MatchResult Pattern::search(
    std::wstring const& text,
    std::shared_ptr<std::atomic_bool> const& cancel) const noexcept
{
    return impl_?impl_->search(text,cancel):MatchResult::NoMatch;
}

} // namespace fxfile::boundedregex
